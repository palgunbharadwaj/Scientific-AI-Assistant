import asyncio
from typing import Dict, Any, List, Optional
from backend.services.pubchem_api import get_compound_by_name
from backend.services.chembl_api import search_molecule

async def resolve_scientific_data(query: str, compound_name: str) -> Dict[str, Any]:
    """
    Executes Parallel Retrieval (PubChem, ChEMBL).
    Returns raw data for the agent to process across its 8 modules.
    """
    # 1. Parallel Retrieval
    tasks = [
        get_compound_by_name(compound_name),
        search_molecule(compound_name)
    ]
    
    pubchem_res, chembl_res = await asyncio.gather(*tasks)
    
    # 2. Extract identifiers
    pc_smiles = pubchem_res.get("canonical_smiles") or ""
    ch_smiles = ""
    if chembl_res.get("molecules"):
        ch_smiles = chembl_res["molecules"][0].get("molecule_structures", {}).get("canonical_smiles", "")
    
    # Needs verification if they disagree
    needs_verification = bool(pc_smiles and ch_smiles and pc_smiles[:10] != ch_smiles[:10])

    return {
        "pubchem": pubchem_res,
        "chembl": chembl_res,
        "needs_verification": needs_verification,
        "compound_found": bool(pc_smiles or ch_smiles)
    }
