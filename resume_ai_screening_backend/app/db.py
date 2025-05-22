import sqlite3
import os

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
        embedding_id TEXT
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
        openai_match_score REAL,
        vector_match_score REAL,
        openai_hr_score REAL,
        applicant_feedback INTEGER,
        recruiter_feedback INTEGER,
        created_at TEXT,
        embedding_id TEXT
    )''')
    conn.commit()
    conn.close()
