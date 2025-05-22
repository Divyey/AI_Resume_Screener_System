import pdfplumber
import re

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def parse_resume(text):
    import re
    name = re.search(r'Name[:\-]?\s*(.*)', text)
    email = re.search(r'[\w\.-]+@[\w\.-]+', text)
    contact = re.search(r'(\+?\d{10,13})', text)
    skills = re.findall(r'(Python|Java|SQL|Machine Learning|Data Science|C\+\+|C#|Javascript|React|Node\.js|AWS)', text, re.I)
    education = re.search(r'(B\.Tech|M\.Tech|PhD|Bachelor|Master|Diploma|UG|PG)', text, re.I)
    experience = re.search(r'(\d+)\s+years?', text)
    return {
        "name": name.group(1).strip() if name else "",
        "email": email.group(0).strip() if email else "",
        "contact": contact.group(1).strip() if contact else "",
        "skills": list(set([s.strip() for s in skills])),
        "education": education.group(1).strip() if education else "",
        "experience": float(experience.group(1)) if experience else 0.0
    }


def parse_jd(text):
    job_title = re.search(r'Job Title[:\-]?\s*(.*)', text)
    responsibilities = re.search(r'Responsibilities[:\-]?\s*(.*)', text)
    skills = re.findall(r'(Python|Java|SQL|Machine Learning|Data Science|C\+\+|C#|Javascript|React|Node\.js|AWS)', text, re.I)
    education = re.search(r'(B\.Tech|M\.Tech|PhD|Bachelor|Master|Diploma|UG|PG)', text, re.I)
    experience = re.search(r'(\d+)\s+years?', text)
    return {
        "jd_job_title": job_title.group(1).strip() if job_title else "",
        "jd_responsibilities": responsibilities.group(1).strip() if responsibilities else "",
        "jd_req_skill": list(set([s.strip() for s in skills])),
        "jd_req_education": education.group(1).strip() if education else "",
        "jd_req_experience": float(experience.group(1)) if experience else 0.0
    }
