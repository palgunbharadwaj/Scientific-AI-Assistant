import requests
from typing import Optional
from backend.config import HUGGINGFACE_API_KEY

# Specialized Chemistry Model on Hugging Face
API_URL = "https://api-inference.huggingface.co/models/AI4Chem/ChemLLM-7B-Chat-1_5-DPO"
headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}" if HUGGINGFACE_API_KEY else ""}

async def call_chem_llm(property_name: str, compound_name: str, context: Optional[str] = None) -> str:
    """
    Calls the ChemLLM-7B model using Chain-of-Thought (ChemCoT) patterns.
    Used as Module 8 (Deep Reasoning) for the Chemistry Agent.
    """
    if not HUGGINGFACE_API_KEY or "PASTE_YOUR" in HUGGINGFACE_API_KEY:
        return "System Notification: Pre-trained ChemLLM-7B is sleeping (No API Key)."

    # ChemCoT Style Prompting
    prompt = f"""
    ### Instruction:
    You are a specialized chemistry assistant. Use Chain-of-Thought (CoT) reasoning.
    Task: Analyze the chemical property '{property_name}' for the compound '{compound_name}'.
    
    ### Context:
    {context if context else "No additional context."}

    ### Response (Chain-of-Thought):
    1. Initial Assessment:
    2. Molecular Structure Considerations:
    3. Property Analysis:
    4. Final Conclusion:
    """

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 800,
            "temperature": 0.1,
            "top_p": 0.95,
            "return_full_text": False
        }
    }

    try:
        # Note: Using synchronous requests here as it's a simple API call, 
        # but in a production async environment, httpx would be preferred.
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        result = response.json()
        
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "No response from model.")
        
        if isinstance(result, dict) and "error" in result:
            return f"ChemLLM Notification: {result['error']}"
            
        return "ChemLLM: Unexpected response format."
    except Exception as e:
        return f"ChemLLM Connection Error: {str(e)}"
