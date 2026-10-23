from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db import Base, engine
from app.models import document, extracted_skill, job_requirement, analysis, recommendation  # noqa: F401
from app.routers import documents, skills, jobs, recommendations, analysis as analysis_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Career Gap Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(skills.router)
app.include_router(jobs.router)
app.include_router(analysis_router.router)
app.include_router(recommendations.router)


@app.get("/health")
def health():
    return {"status": "ok"}
