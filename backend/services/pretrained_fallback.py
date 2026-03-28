"""
Pre-Trained Model Fallback Service.
NO HARDCODED KNOWLEDGE - Returns empty list to force LLM synthesis.
"""
from typing import List, Optional

def deep_search(query: str, top_k: int = 3) -> List[dict]:
    """
    Fallback search: Returns empty to ensure zero template bias.
    Gemini handles synthesis with its own knowledge if APIs fail.
    """
    return []

def get_fallback_info() -> dict:
    return {
        "status": "autonomous_fallback_active",
        "knowledge_source": "gemini_synthesis_engine"
    }
