"""
External API Layer — OpenFDA Drug Information Integration.
Fetches drug labels, adverse events, and recall data from FDA.
"""
import aiohttp

FDA_BASE = "https://api.fda.gov/drug"


async def get_drug_label(drug_name: str) -> dict:
    """Fetch FDA drug label (side effects, indications, warnings)."""
    url = f"{FDA_BASE}/label.json?search=openfda.brand_name:{drug_name}&limit=1"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 404:
                    return {"source": "FDA", "result": f"No label found for '{drug_name}'"}
                if resp.status != 200:
                    return {"error": f"FDA API returned status {resp.status}"}
                data = await resp.json()
                results = data.get("results", [{}])[0]
                return {
                    "source": "FDA",
                    "drug_name": drug_name,
                    "brand_name": results.get("openfda", {}).get("brand_name", ["N/A"])[0],
                    "generic_name": results.get("openfda", {}).get("generic_name", ["N/A"])[0],
                    "manufacturer": results.get("openfda", {}).get("manufacturer_name", ["N/A"])[0],
                    "indications": results.get("indications_and_usage", ["N/A"])[0][:500] + "..." if results.get("indications_and_usage") else "N/A",
                    "warnings": results.get("warnings", ["N/A"])[0][:500] + "..." if results.get("warnings") else "N/A",
                    "adverse_reactions": results.get("adverse_reactions", ["N/A"])[0][:500] + "..." if results.get("adverse_reactions") else "N/A",
                    "contraindications": results.get("contraindications", ["N/A"])[0][:300] + "..." if results.get("contraindications") else "N/A",
                }
        except aiohttp.ClientConnectorError:
            return {"error": "FDA API unreachable. Check network."}
        except Exception as e:
            return {"error": str(e)}


async def get_drug_adverse_events(drug_name: str, limit: int = 5) -> dict:
    """Fetch top adverse event reports for a drug from FDA FAERS."""
    url = f"{FDA_BASE}/event.json?search=patient.drug.medicinalproduct:{drug_name}&count=patient.reaction.reactionmeddrapt.exact&limit={limit}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 404:
                    return {"source": "FDA FAERS", "result": f"No adverse events found for '{drug_name}'"}
                if resp.status != 200:
                    return {"error": f"FDA FAERS returned status {resp.status}"}
                data = await resp.json()
                events = [
                    {"reaction": item["term"], "count": item["count"]}
                    for item in data.get("results", [])
                ]
                return {
                    "source": "FDA FAERS",
                    "drug_name": drug_name,
                    "top_adverse_events": events,
                }
        except Exception as e:
            return {"error": str(e)}
