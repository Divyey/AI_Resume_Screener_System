import openai
import os
import json
import re
from dotenv import load_dotenv
import spacy

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load spaCy English model once globally
nlp = spacy.load("en_core_web_sm")

def extract_job_title(jd_text):
    doc = nlp(jd_text)

    # 1. Try to find a line starting with "Job Title" or similar and extract noun chunks after it
    for line in jd_text.split('\n'):
        if "job title" in line.lower():
            line_doc = nlp(line)
            # Extract noun chunks from this line
            noun_chunks = [chunk.text.strip() for chunk in line_doc.noun_chunks]
            if noun_chunks:
                return noun_chunks[0]

    # 2. Use named entities of type WORK_OF_ART, ORG, or PRODUCT as candidates
    candidates = [ent.text for ent in doc.ents if ent.label_ in ("WORK_OF_ART", "ORG", "PRODUCT")]
    if candidates:
        return candidates[0]

    # 3. Use the first noun chunk in the document as fallback
    noun_chunks = list(doc.noun_chunks)
    if noun_chunks:
        return noun_chunks[0].text.strip()

    # 4. Final fallback
    return "the given role"


def get_openai_match_score(jd_text, resume_text):
    job_title = extract_job_title(jd_text)
    prompt = f"""
        You are an expert recruiter and candidate evaluator, specializing in hiring for {job_title} roles.

        Your task:
        - Carefully analyze the candidate's resume and the job description.
        - Evaluate the candidate's experience, skills, education, and achievements.
        - Compare these to the requirements and expectations of the job description, even if the JD is incomplete or vague (infer typical requirements for this role if needed).
        - Consider not just keywords, but also semantic relevance, structure, and the overall quality of the match.
        - Penalize missing or irrelevant experience/skills, and reward clear alignment.
        - Be objective and critical—do not give perfect scores unless the match is truly exceptional.

        Scoring:
        - Output a single numeric score between 0.000 and 100.000 (with three decimal places, e.g., 78.532).
        - Do not include any explanation, comments, or extra text—output only the number.

        Job Description:
        {jd_text}

        Resume:
        {resume_text}

        Score:
        """.strip()
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "You are a professional AI resume screener."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=8,
            temperature=0
        )
        score_str = response.choices[0].message.content.strip()
        match = re.search(r"\d{1,3}\.\d{3}", score_str)
        score = float(match.group(0)) if match else 0.0
    except Exception as e:
        print(f"OpenAI error: {e}")
        score = 0.0
    return score

def extract_resume_info_with_gpt4o_mini(resume_text):
    prompt = (
        "Extract the following fields from this resume:\n"
        "- Name\n- Email\n- Contact Number\n- Location (city, state, country or address)\n"
        "- Skills\n- Education\n- Experience (in years)\n\n"
        "Return the result as a JSON object.\n\n"
        f"Resume:\n{resume_text}\n"
    )
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",  # or "gpt-3.5-turbo" if you don't have gpt-4o access
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts structured information from resumes."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=512,
            temperature=0.0,
        )
        message_content = response.choices[0].message.content
        match = re.search(r"\{.*\}", message_content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return {"error": "Failed to parse JSON", "raw": message_content}
        else:
            return {"raw_response": message_content}
    except Exception as e:
        print(f"OpenAI error: {e}")
        return {"error": str(e)}