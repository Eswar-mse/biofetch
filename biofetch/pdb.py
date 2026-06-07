"""RCSB PDB REST API fetcher for protein structures."""
import requests
import time
from typing import Optional


PDB_ENTRY_URL = "https://data.rcsb.org/rest/v1/core/entry/{pdb_id}"
PDB_FASTA_URL = "https://www.rcsb.org/fasta/entry/{pdb_id}"
PDB_STRUCT_URL = "https://files.rcsb.org/download/{pdb_id}.pdb"
PDB_CIF_URL = "https://files.rcsb.org/download/{pdb_id}.cif"
PDB_SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
PDB_POLYMER_URL = "https://data.rcsb.org/rest/v1/core/polymer_entity/{pdb_id}/1"


def fetch_pdb_metadata(pdb_id: str, retries: int = 3) -> dict:
    """Fetch entry metadata from RCSB PDB."""
    pdb_id = pdb_id.upper().strip()
    url = PDB_ENTRY_URL.format(pdb_id=pdb_id)

    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
            else:
                raise RuntimeError(f"PDB metadata fetch failed for {pdb_id}: {e}")


def fetch_pdb_structure(pdb_id: str, fmt: str = "pdb", retries: int = 3) -> Optional[str]:
    """Download PDB or CIF structure file."""
    pdb_id = pdb_id.upper().strip()
    url = PDB_STRUCT_URL.format(pdb_id=pdb_id) if fmt == "pdb" else PDB_CIF_URL.format(pdb_id=pdb_id)

    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
            else:
                raise RuntimeError(f"PDB structure fetch failed for {pdb_id}: {e}")


def fetch_pdb_fasta(pdb_id: str, retries: int = 3) -> Optional[str]:
    """Fetch FASTA sequence from PDB entry."""
    pdb_id = pdb_id.upper().strip()
    url = PDB_FASTA_URL.format(pdb_id=pdb_id)

    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
            else:
                raise RuntimeError(f"PDB FASTA fetch failed for {pdb_id}: {e}")


def search_pdb(query: str, max_results: int = 10) -> list[dict]:
    """Full-text search RCSB PDB."""
    payload = {
        "query": {
            "type": "terminal",
            "service": "full_text",
            "parameters": {"value": query}
        },
        "return_type": "entry",
        "request_options": {
            "paginate": {"start": 0, "rows": max_results},
            "results_content_type": ["experimental"],
            "sort": [{"sort_by": "score", "direction": "desc"}],
        }
    }

    try:
        resp = requests.post(PDB_SEARCH_URL, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for hit in data.get("result_set", []):
            results.append({
                "pdb_id": hit.get("identifier", ""),
                "score": round(hit.get("score", 0), 3),
            })
        return results
    except Exception as e:
        raise RuntimeError(f"PDB search failed: {e}")


def extract_pdb_summary(meta: dict, pdb_id: str) -> dict:
    """Extract clean summary from raw PDB metadata JSON."""
    struct = meta.get("struct", {})
    entry = meta.get("entry", {})
    exptl = meta.get("exptl", [{}])
    cell = meta.get("cell", {})
    refine = meta.get("refine", [{}])
    rcsb_entry = meta.get("rcsb_entry_info", {})

    r_free = None
    r_work = None
    if refine:
        r_free = refine[0].get("ls_rfactor_rfree")
        r_work = refine[0].get("ls_rfactor_rwork")

    return {
        "pdb_id": pdb_id.upper(),
        "title": struct.get("title", "N/A"),
        "method": exptl[0].get("method", "N/A") if exptl else "N/A",
        "resolution": rcsb_entry.get("resolution_combined", [None])[0] if rcsb_entry.get("resolution_combined") else None,
        "r_free": r_free,
        "r_work": r_work,
        "deposition_date": entry.get("id", ""),
        "polymer_count": rcsb_entry.get("deposited_polymer_entity_count") or rcsb_entry.get("deposited_polymer_monomer_count", 0),
        "atom_count": rcsb_entry.get("deposited_atom_count", 0),
        "organism": rcsb_entry.get("polymer_entity_taxonomy_count", "N/A"),
    }
