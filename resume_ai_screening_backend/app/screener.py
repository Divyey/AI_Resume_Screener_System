from .db import get_db
from .faiss_db import search_index
from .embeddings import get_embedding
import numpy as np

def filter_and_rank_resumes(jd_text, skills, education_level, min_experience, top_k):
    conn = get_db()
    c = conn.cursor()
    # Filter resumes by experience
    c.execute("""
        SELECT * FROM resumes
        WHERE experience >= ?
    """, (min_experience,))
    resumes = [dict(row) for row in c.fetchall()]
    # Filter by education and skills
    filtered = []
    for r in resumes:
        if education_level.lower() in (r['education'] or '').lower():
            if any(skill.lower() in (r['skills'] or '').lower() for skill in skills):
                filtered.append(r)
    # Get JD embedding
    jd_embedding = get_embedding(jd_text)
    # Compute vector match scores
    for r in filtered:
        try:
            resume_embedding = np.fromstring(r['embedding_id'], sep=',')
            r['vector_match_score'] = float(np.dot(jd_embedding, resume_embedding) / (np.linalg.norm(jd_embedding) * np.linalg.norm(resume_embedding)))
        except Exception:
            r['vector_match_score'] = 0.0
    # Sort by openai_match_score and vector_match_score
    filtered.sort(key=lambda x: ((x['openai_match_score'] or 0), x['vector_match_score']), reverse=True)
    return filtered[:top_k]
