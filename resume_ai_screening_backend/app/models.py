from pydantic import BaseModel
from typing import List, Optional

class JD(BaseModel):
    jd_id: int
    jd_job_title: str
    jd_responsibilities: str
    jd_req_education: str
    jd_req_skill: List[str]
    jd_req_experience: float

class Resume(BaseModel):
    resume_id: int
    name: str
    contact: str
    email: str
    links: List[str]
    pdf_path: str
    education: str
    skills: List[str]
    experience: float
    jd_id_applying_to: Optional[int]
    resume_score: Optional[float]
    openai_match_score: Optional[float]
    vector_match_score: Optional[float]
    openai_hr_score: Optional[float]
    applicant_feedback: Optional[int]
    recruiter_feedback: Optional[int]
    created_at: str
    embedding_id: str
