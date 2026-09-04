from pydantic import BaseModel


class AskRequest(BaseModel):
    symbol: str
    question: str


class AskResponse(BaseModel):
    answer: str
    evidence: list[str]
    confidence: float
    """0-1. Mirrors the change bundle's data-quality confidence, not the LLM's
    certainty -- the LLM has no way to know if its own answer is correct."""
    llm_generated: bool
    """False when GEMINI_API_KEY isn't set: answer is a deterministic,
    evidence-only summary instead of an LLM-generated explanation."""
