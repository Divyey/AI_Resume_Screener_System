import openai
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def get_openai_match_score(jd_text, resume_text):
    # Mini-prompt
    # prompt = (
    #     "Rate how well this resume matches the following job description on a scale of 0-100. "
    #     "Give only the score.\n\n"
    #     f"Job Description:\n{jd_text}\n\nResume:\n{resume_text}\n\nScore:"
    # )
    prompt = (
    "You are an expert Technical HR Manager specializing in Data Science, Full Stack Development, Web Development, "
    "Big Data, Data Engineering, DevOps, and Data Analysis roles.\n\n"
    "Evaluate the following resume against the provided job description.\n"
    "Score how well the resume matches the job description on a scale of 0.00 to 100.00 \n"
    "Return only the numeric score. Do not include explanations or comments.\n\n"
    f"Job Description:\n{jd_text}\n\nResume:\n{resume_text}\n\nScore:"
    )
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=4,
        temperature=0
    )
    try:
        score = float(response.choices[0].text.strip())
    except Exception:
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

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # "gpt-4" not available in 0.28.0; use "gpt-4" or "gpt-3.5-turbo"
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts structured information from resumes."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=512,
        temperature=0.0,
    )

    # Extract the JSON from the response
    message_content = response.choices[0].message["content"]
    match = re.search(r"\{.*\}", message_content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON", "raw": message_content}
    else:
        return {"raw_response": message_content}
