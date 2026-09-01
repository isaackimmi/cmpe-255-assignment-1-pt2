from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok", "project": "05_data_science_skills_lab", "artifact_backed": True}
