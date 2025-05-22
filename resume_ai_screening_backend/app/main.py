############################### S P A C Y ###############################
import os
import uuid
import re
import sqlite3
from datetime import datetime
from typing import List, Optional

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import spacy
import pdfplumber

from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
# ---- Embedding & FAISS Setup ----

EMBED_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
FAISS_INDEX_PATH = 'data/resume_faiss.index'
FAISS_ID_MAP_PATH = 'data/resume_id_map.npy'

def get_embedding(text):
    emb = EMBED_MODEL.encode([text], normalize_embeddings=True)
    return emb[0]

def load_faiss_index():
    if os.path.exists(FAISS_INDEX_PATH):
        index = faiss.read_index(FAISS_INDEX_PATH)
        id_map = np.load(FAISS_ID_MAP_PATH, allow_pickle=True).item()
    else:
        dim = EMBED_MODEL.get_sentence_embedding_dimension()
        index = faiss.IndexFlatIP(dim)
        id_map = {}
    return index, id_map

def save_faiss_index(index, id_map):
    faiss.write_index(index, FAISS_INDEX_PATH)
    np.save(FAISS_ID_MAP_PATH, id_map)

# ---- Database Setup ----

DB_PATH = 'data/resume_screening.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    os.makedirs('data', exist_ok=True)
    conn = get_db()
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS jds (
        jd_id INTEGER PRIMARY KEY AUTOINCREMENT,
        jd_job_title TEXT,
        jd_responsibilities TEXT,
        jd_req_education TEXT,
        jd_req_skill TEXT,
        jd_req_experience REAL,
        embedding_id TEXT,
        embedding_vector BLOB
    )''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS resumes (
        resume_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        contact TEXT,
        email TEXT,
        location TEXT,
        links TEXT,
        pdf_path TEXT,
        education TEXT,
        skills TEXT,
        experience REAL,
        jd_id_applying_to INTEGER,
        resume_score REAL,
        spacy_match_score REAL,
        vector_match_score REAL,
        applicant_feedback INTEGER,
        recruiter_feedback INTEGER,
        created_at TEXT,
        embedding_id TEXT,
        embedding_vector BLOB
    )''')
    conn.commit()
    conn.close()

# ---- FastAPI App Setup ----

app = FastAPI()

origins = [
    "http://localhost:5173",   # Your frontend origin
    "http://localhost:3000",   # Add other origins if needed
    "*",                       # Or use "*" to allow all (not recommended for production)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    create_tables()
    os.makedirs("data/resumes", exist_ok=True)
    os.makedirs("data/jds", exist_ok=True)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the error here if you want
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check backend logs."},
        headers={"Access-Control-Allow-Origin": "*"}  # Add CORS header here too
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={"Access-Control-Allow-Origin": "*"}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return await request_validation_exception_handler(request, exc)

# ---- SpaCy Resume Parser ----

nlp = spacy.load("en_core_web_sm")

def parse_resume_with_spacy(resume_text: str) -> dict:
    doc = nlp(resume_text)
    email_match = re.search(r'[\w\.-]+@[\w\.-]+', resume_text)
    phone_match = re.search(r'(\+?\d[\d\s\-]{8,}\d)', resume_text)
    links = re.findall(r'(https?://[^\s]+)', resume_text)
    tool_words = {"python", "pandas", "excel", "sql", "tableau", "powerbi", "git", "jupyter", "matplotlib", "numpy"}
    # Name
    name = ""
    for ent in doc.ents:
        if ent.label_ == "PERSON" and ent.text.lower() not in tool_words:
            name = ent.text.strip()
            break
    if not name:
        first_line = resume_text.split('\n')[0].strip()
        if not re.match(r'[\w\.-]+@[\w\.-]+', first_line) and first_line.lower() not in tool_words:
            name = first_line
    # Education
    education = ""
    for line in resume_text.split('\n'):
        if re.search(r'\b(B\.?Tech|B\.?Sc|M\.?Sc|M\.?Tech|Bachelor|Master|Ph\.?D|B\.?A\.?|M\.?A\.?|B\.?E\.?)\b', line, re.I):
            education = line.strip()
            break
    # Skills
    skills = ""
    skill_lines = []
    skill_section = False
    for line in resume_text.split('\n'):
        if re.search(r'\bskills?\b', line, re.I):
            skill_section = True
            continue
        if skill_section:
            if line.strip() == "" or re.match(r'^[A-Z][a-z]+:', line):
                break
            skill_lines.append(line.strip())
    if skill_lines:
        skills = ', '.join([s.strip('•- ') for s in skill_lines if s and len(s) < 60])
    # Experience
    experience = 0.0
    exp_match = re.search(r'(\d+)\s*(?:years?|yrs?)', resume_text, re.I)
    if exp_match:
        experience = float(exp_match.group(1))
    # Location
    location = ""
    for ent in doc.ents:
        if ent.label_ == "GPE" and ent.text.strip() != name:
            location = ent.text.strip()
            break
    if not location:
        loc_match = re.search(r'Location:\s*(.*)', resume_text)
        if loc_match:
            location = loc_match.group(1).strip()
    if not location:
        city_state_country = re.search(r'\b([A-Z][a-z]+(?:, [A-Z][a-z]+)*(?:, [A-Z][a-z]+)?)\b', resume_text)
        if city_state_country:
            location = city_state_country.group(1).strip()
    return {
        "name": name.strip(),
        "contact": phone_match.group(1).strip() if phone_match else "",
        "email": email_match.group(0).strip() if email_match else "",
        "location": location.strip(),
        "links": ', '.join([l.strip() for l in links]),
        "education": education.strip(),
        "skills": skills.strip(),
        "experience": experience
    }

# ---- PDF Extraction ----

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# ---- Scoring Functions ----

def spacy_match_score(resume_text, jd_text):
    resume_words = set(re.findall(r'\w+', resume_text.lower()))
    jd_words = set(re.findall(r'\w+', jd_text.lower()))
    if not jd_words:
        return 0.0
    overlap = resume_words & jd_words
    return round(100 * len(overlap) / len(jd_words), 2)

# ---- Endpoints ----

@app.post("/ai_screener/")
async def ai_screener(
    resumes: List[UploadFile] = File(...),
    jd_file: Optional[UploadFile] = File(None),
    jd_text: Optional[str] = Form(None),
    top_k: int = Form(5)
):
    if jd_file:
        jd_pdf_path = f"data/jds/{jd_file.filename}"
        with open(jd_pdf_path, "wb") as f:
            f.write(await jd_file.read())
        jd_content = extract_text_from_pdf(jd_pdf_path)
    elif jd_text:
        jd_content = jd_text
    else:
        raise HTTPException(status_code=400, detail="Provide either a JD PDF or JD text.")

    jd_embedding = get_embedding(jd_content).astype(np.float32)
    jd_embedding_bytes = jd_embedding.tobytes()
    jd_embedding_id = str(uuid.uuid4())
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO jds (jd_job_title, jd_responsibilities, jd_req_education, jd_req_skill, jd_req_experience, embedding_id, embedding_vector)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        "", jd_content, "", "", 0.0, jd_embedding_id, jd_embedding_bytes
    ))
    jd_id = c.lastrowid
    conn.commit()

    index, id_map = load_faiss_index()
    results = []

    for file in resumes:
        pdf_path = f"data/resumes/{file.filename}"
        with open(pdf_path, "wb") as f:
            f.write(await file.read())
        resume_text = extract_text_from_pdf(pdf_path)
        parsed = parse_resume_with_spacy(resume_text)
        resume_embedding = get_embedding(resume_text).astype(np.float32)
        resume_embedding_bytes = resume_embedding.tobytes()
        now = datetime.now().isoformat()
        embedding_id = str(uuid.uuid4())
        c.execute('''
            INSERT INTO resumes (name, contact, email, location, links, pdf_path, education, skills, experience,
                                 jd_id_applying_to, created_at, embedding_id, embedding_vector)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            parsed["name"], parsed["contact"], parsed["email"], parsed["location"], parsed["links"], pdf_path,
            parsed["education"], parsed["skills"], parsed["experience"], jd_id, now, embedding_id, resume_embedding_bytes
        ))
        resume_id = c.lastrowid
        # Add to FAISS index and id_map
        index.add(np.expand_dims(resume_embedding, axis=0))
        id_map[index.ntotal - 1] = resume_id
        # Vector similarity (cosine, since embeddings are normalized)
        vector_score = float(np.dot(jd_embedding, resume_embedding) * 100)
        spacy_score = spacy_match_score(resume_text, jd_content)
        resume_score = round((spacy_score + vector_score) / 2, 2)
        results.append({
            "resume_id": resume_id,
            "name": parsed["name"],
            "contact": parsed["contact"],
            "email": parsed["email"],
            "location": parsed["location"],
            "links": parsed["links"],
            "pdf_path": pdf_path,
            "education": parsed["education"],
            "skills": parsed["skills"],
            "experience": parsed["experience"],
            "jd_id_applying_to": jd_id,
            "resume_score": resume_score,
            "spacy_match_score": spacy_score,
            "vector_match_score": vector_score,
            "applicant_feedback": None,
            "recruiter_feedback": None,
            "created_at": now,
            "embedding_id": embedding_id
        })
    conn.commit()
    conn.close()
    save_faiss_index(index, id_map)
    sorted_results = sorted(results, key=lambda x: x["resume_score"], reverse=True)[:top_k]
    return sorted_results

@app.post("/similarity_search/")
async def similarity_search(
    query_text: Optional[str] = Form(None),
    query_file: Optional[UploadFile] = File(None),
    top_k: int = Form(5)
):
    if query_file:
        file_path = f"data/query_{uuid.uuid4().hex}.pdf"
        with open(file_path, "wb") as f:
            f.write(await query_file.read())
        query_content = extract_text_from_pdf(file_path)
        os.remove(file_path)
    elif query_text:
        query_content = query_text
    else:
        raise HTTPException(status_code=400, detail="Provide either a query PDF or query text.")

    query_embedding = get_embedding(query_content).astype(np.float32)
    index, id_map = load_faiss_index()
    if index.ntotal == 0:
        return JSONResponse({"results": []})

    D, I = index.search(np.expand_dims(query_embedding, axis=0), top_k)
    faiss_indices = I[0]
    similarities = D[0]
    resume_ids = [id_map.get(idx) for idx in faiss_indices if idx in id_map]

    conn = get_db()
    c = conn.cursor()
    results = []
    for i, resume_id in enumerate(resume_ids):
        if resume_id is None:
            continue
        c.execute("SELECT * FROM resumes WHERE resume_id=?", (resume_id,))
        row = c.fetchone()
        if row:
            result = dict(row)
            result["vector_match_score"] = float(similarities[i] * 100)
            result.pop("embedding_vector", None)  # <-- Remove binary field!
            results.append(result)
    conn.close()
    results = sorted(results, key=lambda x: x["vector_match_score"], reverse=True)
    return {"results": results}

@app.post("/clear_db/")
def clear_db():
    try:
        os.remove(DB_PATH)
        if os.path.exists(FAISS_INDEX_PATH):
            os.remove(FAISS_INDEX_PATH)
        if os.path.exists(FAISS_ID_MAP_PATH):
            os.remove(FAISS_ID_MAP_PATH)
        create_tables()
        return {"status": "Database and FAISS index cleared and reset."}
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"message": "Resume AI Screening Backend (SpaCy + FAISS) is running."}
