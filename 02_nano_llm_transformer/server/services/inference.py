"""Use-case functions for bounded deterministic inference."""
from ml.inference import generate, probabilities

def generate_payload(prompt: str, max_new_tokens: int, temperature: float) -> dict:
    return generate(prompt, max_new_tokens, temperature)

def probability_payload(context: str) -> dict:
    return {"context": context, "candidates": probabilities(context)}
