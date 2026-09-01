"""Validated HTTP request contracts."""
from pydantic import BaseModel, Field

class GenerationRequest(BaseModel):
    prompt: str = Field(default="", max_length=500)
    max_new_tokens: int = Field(default=16, ge=1, le=80)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)

class ProbabilityRequest(BaseModel):
    context: str = Field(default="", max_length=200)
