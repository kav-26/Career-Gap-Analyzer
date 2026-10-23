# Career Gap Analyzer

Backend steps included: 1 upload + parsing, 2 skill extraction, 3 job requirement extraction,
4 matching + gap analysis.

## Run (Windows)
    cd backend
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    copy .env.example .env      (then edit .env with your LLM key)
    uvicorn app.main:app --reload

Open http://localhost:8000/docs  -> sections: documents, skills, jobs, analysis
Sample test files are in eval/samples/
