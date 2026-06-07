"""UniProt REST API fetcher for protein records."""
import requests
import time
from typing import Optional


UNIPROT_BASE = "https://rest.uniprot.org/uniprotkb"
UNIPROT_SEARCH = "https://rest.uniprot.org/uniprotkb/search"


FORMAT_MIME = {
    "fasta": "text/plain",
    "json": "application/json",
    "txt": "text/plain",
    "xml": "application/xml",
    "tsv": "text/tsv",
    "gff": "text/gff",
}

FORMAT_SUFFIX = {
    "fasta": ".fasta",
    "json": ".json",
    "txt": ".txt",
    "xml": ".xml",
    "tsv": ".tsv",
}


def fetch_uniprot(
    accession: str,
    fmt: str = "fasta",
    retries: int = 3,
) -> Optional[str]:
    """Fetch a UniProt record by accession ID."""
    fmt = fmt.lower()
    suffix = FORMAT_SUFFIX.get(fmt, ".fasta")
    url = f"{UNIPROT_BASE}/{accession}{suffix}"

    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
            else:
                raise RuntimeError(f"UniProt fetch failed for {accession}: {e}")


def search_uniprot(
    query: str,
    max_results: int = 10,
    reviewed: bool = False,
) -> list[dict]:
    """Search UniProt and return list of hit metadata."""
    fields = "accession,id,protein_name,organism_name,length,reviewed,gene_names"
    params = {
        "query": query + (" AND reviewed:true" if reviewed else ""),
        "format": "json",
        "size": max_results,
        "fields": fields,
    }
    resp = requests.get(UNIPROT_SEARCH, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    results = []
    for entry in data.get("results", []):
        pname = entry.get("proteinDescription", {})
        recommended = pname.get("recommendedName", {})
        full_name = recommended.get("fullName", {}).get("value", "")
        if not full_name:
            submitted = pname.get("submissionNames", [{}])
            full_name = submitted[0].get("fullName", {}).get("value", "") if submitted else ""

        gene_names = entry.get("genes", [])
        gene = gene_names[0].get("geneName", {}).get("value", "") if gene_names else ""

        results.append({
            "accession": entry.get("primaryAccession", ""),
            "entry_name": entry.get("uniProtkbId", ""),
            "protein_name": full_name,
            "gene": gene,
            "organism": entry.get("organism", {}).get("scientificName", ""),
            "length": entry.get("sequence", {}).get("length", 0),
            "reviewed": entry.get("entryType", "") == "UniProtKB reviewed (Swiss-Prot)",
        })
    return results


def fetch_uniprot_metadata(accession: str) -> dict:
    """Fetch full JSON metadata for a UniProt entry."""
    url = f"{UNIPROT_BASE}/{accession}.json"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.json()


def extract_uniprot_summary(meta: dict) -> dict:
    """Extract a clean summary from raw UniProt JSON."""
    pname = meta.get("proteinDescription", {})
    recommended = pname.get("recommendedName", {})
    full_name = recommended.get("fullName", {}).get("value", "N/A")

    gene_names = meta.get("genes", [])
    gene = gene_names[0].get("geneName", {}).get("value", "N/A") if gene_names else "N/A"

    organism = meta.get("organism", {})
    seq = meta.get("sequence", {})

    functions = []
    for comment in meta.get("comments", []):
        if comment.get("commentType") == "FUNCTION":
            for text in comment.get("texts", []):
                functions.append(text.get("value", ""))

    keywords = [kw.get("name", "") for kw in meta.get("keywords", [])]

    return {
        "accession": meta.get("primaryAccession", ""),
        "entry_name": meta.get("uniProtkbId", ""),
        "protein_name": full_name,
        "gene": gene,
        "organism": organism.get("scientificName", "N/A"),
        "taxonomy": " > ".join([t.get("scientificName", "") for t in organism.get("lineage", [])[-3:]]),
        "length": seq.get("length", 0),
        "mass": seq.get("molWeight", 0),
        "reviewed": "Swiss-Prot" in meta.get("entryType", ""),
        "function": functions[0][:300] + "..." if functions and len(functions[0]) > 300 else (functions[0] if functions else "N/A"),
        "keywords": keywords[:10],
    }
