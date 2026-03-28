"""
Prescription Evaluation Modules — DPEA 7-Module Logic.
Purger: No hardcoded sentences. Returns raw attributes for Gemini.
"""
from typing import Optional, List, Dict

def task_decomposer(query: str, drug_name: str) -> Dict:
    """[Module 1: TaskDecomposer] Clinical breakdown."""
    return {"subtasks": ["composition_check", "claim_verification", "ddi_scanning", "suitability_review"], "target": drug_name}

def drug_composition_analysis(mol_data: Dict) -> Dict:
    """[Module 2: DrugComposition] Raw markers."""
    smiles = mol_data.get("canonical_smiles", "").upper()
    return {"has_benzene": "C1=CC=CC=C1" in smiles, "has_nitrogen": "N" in smiles, "is_organic": "C" in mol_data.get("molecular_formula", "").upper()}

def medical_claim_verifier(query: str, fda_label: Dict) -> Dict:
    """[Module 3: Claim Verifier] Match status."""
    indications = fda_label.get("indications_and_usage", "").lower()
    conditions = ["diabetes", "hypertension", "pain", "infection", "cancer", "fever"]
    found = [c for c in conditions if c in query.lower()]
    return {"verified": [c for c in found if c in indications], "off_label": [c for c in found if c not in indications]}

def drug_drug_interaction_logic(query: str, drug_name: str) -> Dict:
    """[Module 4: DDI Logic] Raw matches."""
    q = query.lower()
    critical_pairs = {"warfarin": ["aspirin", "ibuprofen"], "insulin": ["alcohol"]}
    interactions = []
    for drug, incompatible in critical_pairs.items():
        if drug in q:
            for bad_drug in incompatible:
                if bad_drug in q and bad_drug != drug_name.lower():
                    interactions.append({"a": drug, "b": bad_drug})
    return {"interactions": interactions, "danger": len(interactions) > 0}

def side_effect_evaluator(adverse_events: List) -> Dict:
    """[Module 5: SideEffect] Raw identifiers."""
    return {"top_effects": [e.get("term", "unspecified") for e in adverse_events[:3]], "count": len(adverse_events)}

def patient_suitability_reasoner(fda_label: Dict) -> Dict:
    """[Module 6: Suitability] Precaution markers."""
    warnings = fda_label.get("warnings", "").lower()
    return {"pregnancy_risk": "pregnancy" in warnings, "pediatric_risk": "children" in warnings}

def internal_evidence_aggregator(pipeline_state: Dict) -> Dict:
    """[Module 7: Aggregator] Core decision data."""
    return {"safe_to_proceed": not pipeline_state.get("ddi_obj", {}).get("danger"), "consensus_met": True}
