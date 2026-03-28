"""
Chemistry Analysis Modules — CRA 7-Module Workflow.
NO SENTENCES - Returns raw attributes for Gemini.
"""
from typing import Optional, List, Dict

HAZARD_MAP = {
    "H200": "unstable explosive", "H220": "extremely flammable gas", "H225": "highly flammable liquid",
    "H300": "fatal if swallowed", "H301": "toxic if swallowed", "H302": "harmful if swallowed",
    "H310": "fatal in contact with skin", "H311": "toxic if skin-contact occurs", "H312": "harmful in contact with skin",
    "H314": "causes severe skin burns and eye damage", "H315": "skin irritant",
    "H330": "fatal if inhaled", "H400": "very toxic to aquatic life"
}

def task_decomposer(query: str, compound_name: str) -> Dict:
    """[Module 1: TaskDecomposer] Research breakdown."""
    return {"subtasks": ["structure_normalization", "hazard_assessment", "stability_analysis", "environmental_score"], "target": compound_name}

def normalize_structure(mol_data: Dict) -> Dict:
    """[Module 2: Structure Normalizer] Raw attributes."""
    smiles = mol_data.get("canonical_smiles", "")
    formula = mol_data.get("molecular_formula", "").upper()
    return {"smiles": smiles, "formula": formula, "is_organic": "C" in formula, "classification": "organic" if "C" in formula else "inorganic"}

def enhanced_safety_analysis(mol_data: Dict) -> Dict:
    """[Module 3: Safety & Toxicity] Raw hazards."""
    hazards = mol_data.get("hazards", [])
    status = "safe"
    if any(c in hazards for c in ["H300", "H301", "H310", "H311", "H330"]): status = "danger"
    elif any(c in hazards for c in ["H302", "H312", "H315", "H225"]): status = "warning"
    return {"status": status, "hazard_descriptions": [HAZARD_MAP[c] for c in hazards if c in HAZARD_MAP], "hazard_codes": hazards}

def reaction_reasoning(mol_data: Dict, safety_status: str) -> Dict:
    """[Module 4: Reaction Reasoning] Functional markers."""
    smiles = mol_data.get("canonical_smiles", "").upper()
    return {"has_oxygen": "O" in smiles, "has_nitrogen": "N" in smiles, "reactivity_level": "high" if safety_status == "danger" else "stable"}

def environmental_sustainability(mol_data: Dict) -> Dict:
    """[Module 5: Sustainability] Numerical indicators."""
    mw = float(mol_data.get("molecular_weight", 0)) if isinstance(mol_data.get("molecular_weight"), (int, float)) else 0
    score = 100 - (15 if mw > 400 else 0)
    return {"score": score, "mw": mw, "high_mass_penalty": mw > 400}

def conceptual_mixing_outcome(safety_status: str, sustain_score: float) -> Dict:
    """[Module 6: Mixing] Predictive attributes."""
    return {"impact": "low" if sustain_score > 75 else "high", "protocol": "hazardous" if safety_status == "danger" else "standard"}

def evidence_aggregator(pipeline_state: Dict) -> Dict:
    """[Module 7: Aggregator] Core summary data."""
    return {"consensus_status": "validated" if pipeline_state.get("safety_obj", {}).get("status") != "danger" else "high_risk", "ready_for_synthesis": True}
