try:
    from google import genai
except ImportError:
    import google.genai as genai
from typing import Optional, List, Dict
from backend.config import GOOGLE_API_KEY

# The "Master Research Prompt" - ENFORCES DATA PROVENANCE & AUTONOMY
MASTER_PROMPT = """
ROLE: You are the Scientific AI Expert.
TASK: {query}

DATA CONTEXT (EXTERNAL AGENTS):
{raw_data}

CONVERSATION HISTORY:
{history}

INSTRUCTIONS:
- HISTORY AWARENESS: If the user query is a repetition or similar to a previous inquiry in the history, provide a **significantly more detailed, deeper, and more analytical explanation** than before. Expand on molecular mechanisms, structural-activity relationships, and clinical implications.
- CONDITIONAL SOURCE DISCLOSURE: If and only if the user explicitly asks for the sources, where the data came from, or how to confirm the response is correct, include a dedicated **Scientific Data Provenance & Sources** section. List the specific external APIs used (PubChem, ChEMBL, or FDA) and provide **UNIQUE CLICKABLE MARKDOWN LINKS** to the official records (e.g., use `https://pubchem.ncbi.nlm.nih.gov/compound/[CID]` for PubChem). If data exists in multiple records, list all unique links once. If they do NOT ask, do not include this section.
- If the task is a GREETING or REDIRECTION, be a professional, polite AI assistant.
- Use **Bold** for headers and bullet points for lists. NEVER use '#' headers.
- Use the PROVIDED DATA CONTEXT (including raw database results and Expert/Deep Reasoning blocks). If absolutely NO DATA or REASONING is available from any source, state it clearly without mentioning technical errors.
- **DEEP REASONING**: If the CRA data includes a `deep_reasoning` field, or the DPEA data includes `clinical_expert_data`, prioritize these advanced insights and Chain-of-Thought (CoT) logic to explain complex molecular properties or clinical risks.
- NO TECHNICAL LEAKS: NEVER mention "PubChem status 404", "initial lookup issues", "molecule key", or the technical "CONTEXT:" block in your response. 
- Maintain 100% data integrity. Do NOT add hypothetical chemistry or medical data.
"""

client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

async def synthesize_narrative(query: str, raw_data: Dict, history: Optional[List[Dict]] = None) -> str:
    """
    Calls Gemini (google-genai) for synthesis with a robust model waterfall.
    Tries multiple specialized model generations to handle quota (429) and naming (404) issues.
    """
    if not client:
        return "System Warning: Google API Key missing or client failed."

    try:
        hist_text = "\\n".join([f"{m['role'].upper()}: {m['content']}" for m in history]) if history else "No previous context."
        full_prompt = MASTER_PROMPT.format(query=query, raw_data=raw_data, history=hist_text)
        
        contents = [{
            "role": "user",
            "parts": [{"text": full_prompt}]
        }]

        # --- COMPREHENSIVE FLASH WATERFALL (ROBUST QUOTA HANDLING) ---
        # We try every major Flash model available to your account in order of speed/quota.
        # If one fails (429 or 404), it automatically falls back to the next one.
        models_to_try = [
            "gemini-2.5-flash", 
            "gemini-2.0-flash", 
            "gemini-2.0-flash-lite", 
            "gemini-flash-latest",
            "gemini-2.0-flash-001",
            "gemini-2.5-flash-lite",
            "gemini-flash-lite-latest"
        ]
        
        for model_name in models_to_try:
            try:
                print(f"[GeminiService] Synthesizing with: {model_name}")
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                # Attempt next model in the list (e.g. if 404 or 429 occurs)
                print(f"[GeminiService] {model_name} failed: {e}")
                continue
        
        return "System Warning: All high-quota Flash models are currently unavailable. Please verify your API key."

    except Exception as e:
        print(f"[GeminiService] Synthesis Failed: {e}")
        error_type = "Quota Exhausted" if "429" in str(e) else ("Model Not Found" if "404" in str(e) else "Internal API Error")
        return f"Research synthesis is currently unavailable ({error_type}). (Error: {str(e)[:100]}...)"

def format_history_for_gemini(history: List[Dict]) -> List[Dict]:
    """Placeholder for history."""
    return []
