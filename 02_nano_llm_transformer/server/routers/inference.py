from fastapi import APIRouter, HTTPException
from server.schemas import GenerationRequest, ProbabilityRequest
from server.services.inference import generate_payload, probability_payload

router = APIRouter(tags=["inference"])

@router.post("/generate")
def generate_text(request: GenerationRequest) -> dict:
    try:
        return generate_payload(request.prompt, request.max_new_tokens, request.temperature)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.post("/probabilities")
def next_probabilities(request: ProbabilityRequest) -> dict:
    try:
        return probability_payload(request.context)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
