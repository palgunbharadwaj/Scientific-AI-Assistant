import requests
import asyncio
from typing import Optional, Dict
from backend.config import HUGGINGFACE_API_KEY

# Clinical Model Endpoints
MODELS = {
    "biogpt": "https://api-inference.huggingface.co/models/microsoft/BioGPT-Large",
    "clinical_bert": "https://api-inference.huggingface.co/models/medicalai/ClinicalBERT",
    "biobert": "https://api-inference.huggingface.co/models/pucpr/biobertpt-clin"
}

headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}" if HUGGINGFACE_API_KEY else ""}

def query_model(model_key: str, prompt: str) -> str:
    """Synchronous helper for HF Inference API."""
    if not HUGGINGFACE_API_KEY or "PASTE_YOUR" in HUGGINGFACE_API_KEY:
        return f"Model {model_key} is offline: Missing API Key."
        
    url = MODELS.get(model_key)
    payload = {"inputs": prompt}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        result = response.json()
        
        # Result formats vary by model type (BERT vs GPT)
        if isinstance(result, list) and len(result) > 0:
            if "generated_text" in result[0]:
                return result[0]["generated_text"]
            return str(result[0])
        return str(result)
    except Exception as e:
        return f"{model_key} Error: {str(e)}"

async def call_clinical_ensemble(query: str, context: Optional[str] = None) -> Dict[str, str]:
    """
    Calls the clinical ensemble: BioGPT (Reasoning), ClinicalBERT (Risk), BioBERT (Verification).
    """
    if not HUGGINGFACE_API_KEY or "PASTE_YOUR" in HUGGINGFACE_API_KEY:
        return {"error": "Clinical Ensemble requires a Hugging Face API Key."}

    # Task-Specific Prompts
    prompts = {
        "biogpt": f"Clinical Reasoning for query: {query}. Context: {context}. Explanation:",
        "clinical_bert": f"Medical Risk Assessment: {query}. Evidence: {context}",
        "biobert": f"Medical Fact Verification: {query}. Data: {context}"
    }

    # Parallel Execution via Threads (since requests is sync)
    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(None, query_model, k, v) 
        for k, v in prompts.items()
    ]
    
    results = await asyncio.gather(*tasks)
    
    return {
        "deep_reasoning": results[0],
        "risk_assessment": results[1],
        "fact_verification": results[2]
    }
