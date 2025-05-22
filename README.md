# AI_Resume_Screener_System 2.0

Resume screening app using **spaCy** and **FAISS DB**.
Full-stack: FastAPI backend + Vite-React frontend.

![Resume Screener 2 0](https://github.com/user-attachments/assets/ecc20fe5-e461-4ad5-a7a4-daf0f69832c5)

---

## Versions

- Python: 3.11.12
- Node.js: v22.14.0
- npm: 10.9.2
- pip: 25.1.1

---

## Major Dependencies

**Backend:**
- fastapi
- spacy (en_core_web_sm)
- faiss-cpu
- sentence-transformers
- pdfminer.six, pdfplumber
- pandas, scikit-learn, torch

**Frontend:**
- react 19
- vite 6
- axios

---

## Quick Start

### 1. Clone the repository

```
git clone https://github.com/Divyey/AI_Resume_Screener_System.git
cd AI_Resume_Screener_System
```

### 2. Backend Setup

```
cd resume_ai_screening_backend
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Frontend Setup

```
cd ../resume_ai_screening_frontend
npm install
```

### 4. Running the App

**Start backend:**
```
cd resume_ai_screening_backend
uvicorn main:app --reload
```

**Start frontend (in a new terminal):**
```
cd resume_ai_screening_frontend
npm run dev
```

Open in your browser.
```
http://localhost:5173/
```
---

## Notes

- No OpenAI API key needed.
- Make sure ports 8000 (backend) and 3000 (frontend) are available.
- For best results, use the specified versions.

