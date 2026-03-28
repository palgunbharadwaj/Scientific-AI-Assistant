import httpx
from typing import Dict, Any

async def resolve_molecule_nih(name: str) -> Dict[str, Any]:
    """
    Tertiary Fallback: Uses NIH CACTUS (NCI) for molecular name resolution.
    Returns SMILES and Formula if found.
    """
    try:
        url = f"https://cactus.nci.nih.gov/chemical/structure/{name}/smiles"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=5.0)
            if resp.status_code == 200:
                smiles = resp.text.strip()
                # Get formula too
                formula_url = f"https://cactus.nci.nih.gov/chemical/structure/{name}/formula"
                formula_resp = await client.get(formula_url, timeout=5.0)
                formula = formula_resp.text.strip() if formula_resp.status_code == 200 else ""
                
                return {
                    "name": name,
                    "smiles": smiles,
                    "molecular_formula": formula,
                    "source": "NIH CACTUS"
                }
    except Exception:
        pass
    return {"error": "NIH resolution failed"}

async def get_drug_info_rxnav(name: str) -> Dict[str, Any]:
    """
    Tertiary Fallback: Uses NIH RXNav for drug information and interactions.
    """
    try:
        url = f"https://rxnav.nlm.nih.gov/REST/drugs.json?name={name}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                # Check if we got any concept groups
                if "drugGroup" in data and "conceptGroup" in data["drugGroup"]:
                    return {
                        "name": name,
                        "rxnav_data": data["drugGroup"]["conceptGroup"],
                        "source": "NIH RXNav"
                    }
    except Exception:
        pass
    return {"error": "RXNav fallback failed"}
