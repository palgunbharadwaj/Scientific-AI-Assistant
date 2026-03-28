"""
Orchestrator: 100% Autonomous Synthesis via Gemini.
Coordinates specialized research agents and synthesizes unified outcomes.
"""
import asyncio
import uuid
from typing import Optional

from backend.models import QueryResponse, TokenData
from backend.services.audit_logger import log_event
from backend.services.database import log_query_to_db, add_chat_message, get_chat_history
from backend.agents.chemistry_agent import run as cra_run
from backend.agents.drug_discovery_agent import run as ddra_run
from backend.agents.prescription_agent import run as dpea_run
from backend.services.shared_utils import refine_query, detect_topic, SCIENTIFIC_DOMAIN_KEYWORDS, GREETINGS
from backend.services.gemini_service import synthesize_narrative

async def orchestrate(
    query: str,
    agent_hint: Optional[str],
    user: TokenData,
) -> QueryResponse:
    """
    Main Brain: Refines query, runs agents, and calls Gemini for ALL natural language.
    """
    # 1. Refinement
    refined_query, clarification, is_on_topic = refine_query(query)
    session_id = user.username or "anonymous"

    # 2. Autonomous Intent Handling via Gemini
    q_low = refined_query.lower().strip("?.! ")
    has_scientific_intent = any(kw in q_low for kw in SCIENTIFIC_DOMAIN_KEYWORDS)
    is_greeting = any(g == q_low for g in GREETINGS) or len(q_low.split()) <= 1

    # --- Scenario A: Non-Scientific or Greeting ---
    if not is_on_topic or (is_greeting and not has_scientific_intent):
        topic = detect_topic(query)
        
        # Define persona based on context
        persona = "Scientific AI Assistant"
        if agent_hint == "CRA":
            persona = "Chemistry Research Agent (CRA)"
        elif agent_hint == "DDRA":
            persona = "Drug Discovery Agent (DDRA)"
        elif agent_hint == "DPEA":
            persona = "Prescription Evaluation Agent (DPEA)"
        
        prompt = f"GREETING_OR_REDIRECT: The user said '{query}'. You are the {persona}. If it's a greeting, be a polite expert and state your name. If off-topic ({topic}), redirect them politely to your area of science. NEVER use the word 'Orchestrator' in your greeting."
        
        response_text = await synthesize_narrative(prompt, {"topic": topic})
        return QueryResponse(
            agent_used="orchestrator",
            result={"summary": response_text, "is_conversational": True},
            message="Autonomous response generated."
        )

    # --- Scenario B: Scientific Research (The Multi-Agent Workflow) ---
    
    # 1. Retrieve History Early for Context-Aware Planning
    history = get_chat_history(session_id, limit=6)
    history_context = ""
    if history:
        history_context = "CONTEXT (Last 6 messages):\n" + "\n".join([f"{m['role']}: {m['content']}" for m in history])
    else:
        history_context = "No previous history."

    # 2. Research Planner: Determine needed agents and flow (Sequential vs Parallel)
    # Pass agent_hint to ensure domain-locking if chatting with a specific agent.
    is_auto = agent_hint is None or agent_hint == "auto"
    planner_prompt = f"""
    RESEARCH_PLANNER: You are the brain of a Multi-Agent Scientific Assistant.
    
    {history_context}

    NEW QUERY: "{refined_query}"
    
    AGENT_RESTRICTION: {agent_hint if not is_auto else 'None - Orchestrator Mode'}

    TASK:
    1. Identify the core drug/compound discussed in context or query.
    2. Determine which specialized agents are REQUIRED for the NEW QUERY:
       - CRA: Chemical structure, molecular properties, or basic identity.
       - DDRA: Biological targets, drug-discovery data, or Mechanism of Action.
       - DPEA: Clinical safety, drug interactions, or prescription guidelines.

    STRICT DOMAIN LOCKING: 
    - If AGENT_RESTRICTION is 'CRA', you MUST NOT use DDRA or DPEA. 
    - If AGENT_RESTRICTION is 'DDRA', you MUST NOT use CRA or DPEA.
    - If AGENT_RESTRICTION is 'DPEA', you MUST NOT use CRA or DDRA.
    - If the user's question belongs to a DIFFERENT domain than AGENT_RESTRICTION, return an empty "agents" list and explain exactly which domain it belongs to in "reasoning".

    JSON OUTPUT ONLY:
    {{
        "agents": ["CRA", "DDRA", "DPEA"], // List ONLY the restricted agent if it fits.
        "mode": "sequential" or "parallel",
        "reasoning": "short explanation"
    }}
    """
    import json
    try:
        plan_raw = await synthesize_narrative(planner_prompt, {"task": "PLANNING"})
        plan_clean = plan_raw.strip().replace("```json", "").replace("```", "")
        plan = json.loads(plan_clean)
    except Exception:
        plan = {"agents": ["CRA", "DDRA", "DPEA"] if is_auto else [agent_hint], "mode": "parallel"}

    needed_agents = plan.get("agents", [])
    
    # --- Check for Domain Mismatch Refusal ---
    if not is_auto and agent_hint and agent_hint not in needed_agents:
        reasoning = plan.get('reasoning', 'Domain mismatch.')
        refusal_summary = f"I am the specialized **{agent_hint} Agent** and I only handle tasks in my specific research domain. {reasoning} For a comprehensive answer involving other agents, please use the **Analytical Orchestrator**."
        
        return QueryResponse(
            agent_used=agent_hint,
            result={
                "agent": agent_hint,
                "status": "refusal",
                "summary": refusal_summary,
                "reasoning": reasoning
            },
            message="Domain Restriction Active."
        )

    # Fallback for Orchestrator if planner is empty
    if is_auto and not needed_agents:
        needed_agents = ["CRA", "DDRA", "DPEA"]

    mode = plan.get("mode", "parallel")
    cra_res, ddra_res, dpea_res = {}, {}, {}

    # 3. Execution with Data Piping
    if mode == "sequential":
        # Order: CRA -> DDRA -> DPEA (The Scientific Pipeline)
        accumulated_context = ""
        if "CRA" in needed_agents:
            cra_res = await cra_run(refined_query)
            accumulated_context += f"\nCRA_CHEMICAL_DATA: {json.dumps(cra_res.get('raw_data', {}))}"
        if "DDRA" in needed_agents:
            ddra_res = await ddra_run(f"{refined_query}\nCONTEXT: {accumulated_context}")
            accumulated_context += f"\nDDRA_DISCOVERY_DATA: {json.dumps(ddra_res.get('raw_data', {}))}"
        if "DPEA" in needed_agents:
            dpea_res = await dpea_run(f"{refined_query}\nCONTEXT: {accumulated_context}")
    else:
        cra_task = cra_run(refined_query) if "CRA" in needed_agents else asyncio.sleep(0, result={})
        ddra_task = ddra_run(refined_query) if "DDRA" in needed_agents else asyncio.sleep(0, result={})
        dpea_task = dpea_run(refined_query) if "DPEA" in needed_agents else asyncio.sleep(0, result={})
        cra_res, ddra_res, dpea_res = await asyncio.gather(cra_task, ddra_task, dpea_task)

    # 4. Combine Data for Final Synthesis
    raw_bundle = {
        "chemistry": cra_res.get("raw_data") if cra_res else None,
        "discovery": ddra_res.get("raw_data") if ddra_res else None,
        "clinical": dpea_res.get("raw_data") if dpea_res else None,
        "compound_name": cra_res.get("compound_name") or ddra_res.get("compound_name") or dpea_res.get("drug_name"),
        "execution_plan": plan
    }

    # 5. Final Autonomous Synthesis
    integrated_report = await synthesize_narrative(refined_query, raw_bundle, history=history)

    # Persistence
    add_chat_message(session_id, "user", refined_query)
    add_chat_message(session_id, "model", integrated_report)
    log_event("QUERY_PROCESSED", user.username, {"agent": "orchestrator", "query": refined_query, "plan": plan})
    log_query_to_db(str(uuid.uuid4()), user.username, "orchestrator", refined_query)

    return QueryResponse(
        agent_used="orchestrator",
        result={
            "agent": "orchestrator",
            "status": "success",
            "summary": integrated_report,
            "raw_data": raw_bundle,
            "compound_name": raw_bundle["compound_name"],
            "plan": plan
        }
    )
