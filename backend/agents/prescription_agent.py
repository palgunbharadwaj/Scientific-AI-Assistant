"""
Prescription Evaluation Agent (DPEA) — Focus: Interaction, Dose, Side Effects.
"""
from typing import Optional, Dict, Any, List
from backend.services.fda_api import get_drug_label
from backend.services.shared_utils import refine_query
from backend.services.prescription_modules import (
    task_decomposer,
    drug_composition_analysis,
    medical_claim_verifier,
    drug_drug_interaction_logic,
    side_effect_evaluator,
    patient_suitability_reasoner,
    internal_evidence_aggregator
)

async def run(query: str, context: Optional[dict] = None) -> dict:
    """
    DPEA Clinical Pipeline.
    Returns ONLY raw analysis data.
    """
    refined_query, clarification, is_on_topic = refine_query(query)
    
    # Extract drug name (heuristic) - Remove any CONTEXT block first
    clean_query = refined_query.split("\nCONTEXT:")[0].split("CONTEXT:")[0].strip()
    drug_name = clean_query.split()[-1].strip("?.")
    
    from backend.services.data_resolver import resolve_scientific_data
    resolution = await resolve_scientific_data(refined_query, drug_name)
    molecule = resolution.get("pubchem") or resolution.get("chembl") or {}

    # Fetch FDA data for clinical modules
    fda_label = await get_drug_label(drug_name)
    adverse_events = fda_label.get("adverse_events", [])

    pipeline_state = {
        "query": refined_query,
        "molecule": molecule,
        "agent": "DPEA"
    }

    # Module 1 & 2
    pipeline_state["decomposer"] = task_decomposer(refined_query, drug_name)
    pipeline_state["composition"] = drug_composition_analysis(molecule)
    
    # Module 3 & 4
    pipeline_state["claim"] = medical_claim_verifier(refined_query, fda_label)
    ddi_obj = drug_drug_interaction_logic(refined_query, drug_name)
    pipeline_state["ddi_obj"] = ddi_obj
    
    # Module 5 & 6
    pipeline_state["side_effects"] = side_effect_evaluator(adverse_events)
    pipeline_state["suitability"] = patient_suitability_reasoner(fda_label)
    
    # Module 7: Aggregator
    pipeline_state["evidence"] = internal_evidence_aggregator(pipeline_state)
    
    # Module 8: Deep Clinical Insights (Multi-Model Ensemble)
    from backend.services.clinical_llm_service import call_clinical_ensemble
    clinical_data = await call_clinical_ensemble(
        query=refined_query,
        context=str(pipeline_state.get("side_effects", "")) + str(pipeline_state.get("suitability", ""))
    )
    pipeline_state["clinical_expert_data"] = clinical_data

    return {
        "agent": "DPEA",
        "status": "success",
        "raw_data": pipeline_state,
        "molecule": molecule,
        "drug_name": drug_name
    }
