"""
External API Layer — ChEMBL Integration.
Fetches drug/molecule data, ADMET properties, and activity data.
"""
import aiohttp
from typing import Optional

CHEMBL_BASE = "https://www.ebi.ac.uk/chembl/api/data"


async def search_molecule(query: str) -> dict:
    """Search ChEMBL for a molecule by name."""
    url = f"{CHEMBL_BASE}/molecule/search?q={query}&format=json&limit=3"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return {"error": f"ChEMBL returned status {resp.status}"}
                data = await resp.json()
                molecules = data.get("molecules", [])
                if not molecules:
                    return {"source": "ChEMBL", "result": "No molecules found", "query": query}
                results = []
                for mol in molecules[:3]:
                    results.append({
                        "chembl_id": mol.get("molecule_chembl_id"),
                        "name": mol.get("pref_name", "Unknown"),
                        "molecular_formula": mol.get("molecule_properties", {}).get("molecular_formula", "N/A"),
                        "molecular_weight": mol.get("molecule_properties", {}).get("full_mwt", "N/A"),
                        "smiles": mol.get("molecule_structures", {}).get("canonical_smiles", "N/A") if mol.get("molecule_structures") else "N/A",
                        "max_phase": mol.get("max_phase", "N/A"),  # clinical trial phase
                        "chembl_url": f"https://www.ebi.ac.uk/chembl/compound_report_card/{mol.get('molecule_chembl_id')}",
                    })
                return {"source": "ChEMBL", "query": query, "molecules": results}
        except aiohttp.ClientConnectorError:
            return {"error": "ChEMBL API unreachable. Check network."}
        except Exception as e:
            return {"error": str(e)}


async def get_drug_indications(chembl_id: str) -> dict:
    """Get approved drug indications for a ChEMBL compound."""
    url = f"{CHEMBL_BASE}/drug_indication?molecule_chembl_id={chembl_id}&format=json"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return {"error": f"ChEMBL indication fetch failed: {resp.status}"}
                data = await resp.json()
                indications = [
                    {
                        "indication": ind.get("mesh_heading", "N/A"),
                        "max_phase": ind.get("max_phase_for_ind", "N/A"),
                        "efo_term": ind.get("efo_term", "N/A"),
                    }
                    for ind in data.get("drug_indications", [])[:5]
                ]
                return {"source": "ChEMBL", "chembl_id": chembl_id, "indications": indications}
        except Exception as e:
            return {"error": str(e)}
