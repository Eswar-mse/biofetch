"""NCBI Entrez fetcher for nucleotide, protein, and gene records."""
import time
from typing import Optional
from Bio import Entrez, SeqIO
import io


# NCBI requires an email for Entrez
Entrez.email = "biofetch-tool@example.com"
Entrez.tool = "BioFetch"


NCBI_DB_MAP = {
    "nucleotide": "nucleotide",
    "nt": "nucleotide",
    "protein": "protein",
    "prot": "protein",
    "gene": "gene",
    "pubmed": "pubmed",
    "taxonomy": "taxonomy",
}

FORMAT_MAP = {
    "fasta": ("fasta", "text"),
    "genbank": ("gb", "text"),
    "gb": ("gb", "text"),
    "xml": ("xml", "xml"),
    "text": ("text", "text"),
}


def search_ncbi(query: str, db: str = "nucleotide", max_results: int = 10) -> dict:
    """Search NCBI and return a list of IDs and metadata."""
    db = NCBI_DB_MAP.get(db.lower(), db)
    handle = Entrez.esearch(db=db, term=query, retmax=max_results, usehistory="y")
    record = Entrez.read(handle)
    handle.close()
    return {
        "ids": record["IdList"],
        "count": int(record["Count"]),
        "webenv": record.get("WebEnv"),
        "query_key": record.get("QueryKey"),
    }


def fetch_ncbi(
    accession: str,
    db: str = "nucleotide",
    fmt: str = "fasta",
    retries: int = 3,
) -> Optional[str]:
    """Fetch a single record from NCBI by accession ID."""
    db = NCBI_DB_MAP.get(db.lower(), db)
    ret_type, ret_mode = FORMAT_MAP.get(fmt.lower(), ("fasta", "text"))

    for attempt in range(retries):
        try:
            handle = Entrez.efetch(
                db=db,
                id=accession,
                rettype=ret_type,
                retmode=ret_mode,
            )
            data = handle.read()
            handle.close()
            if isinstance(data, bytes):
                data = data.decode("utf-8", errors="replace")
            return data
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
            else:
                raise RuntimeError(f"NCBI fetch failed for {accession}: {e}")


def fetch_ncbi_summary(accession: str, db: str = "nucleotide") -> Optional[dict]:
    """Fetch DocSum metadata for a record."""
    db = NCBI_DB_MAP.get(db.lower(), db)
    handle = Entrez.esummary(db=db, id=accession)
    records = Entrez.read(handle)
    handle.close()
    if records:
        return dict(records[0])
    return None


def parse_fasta_stats(fasta_text: str) -> list[dict]:
    """Parse FASTA text and return basic stats per record."""
    stats = []
    handle = io.StringIO(fasta_text)
    for record in SeqIO.parse(handle, "fasta"):
        seq = str(record.seq)
        length = len(seq)
        gc = (seq.upper().count("G") + seq.upper().count("C")) / length * 100 if length else 0
        stats.append({
            "id": record.id,
            "description": record.description,
            "length": length,
            "gc_percent": round(gc, 2),
        })
    return stats


def batch_fetch_ncbi(
    accessions: list[str],
    db: str = "nucleotide",
    fmt: str = "fasta",
    delay: float = 0.4,
) -> dict[str, str]:
    """Batch fetch multiple accessions with rate limiting."""
    results = {}
    for acc in accessions:
        try:
            data = fetch_ncbi(acc, db=db, fmt=fmt)
            results[acc] = data
        except Exception as e:
            results[acc] = f"ERROR: {e}"
        time.sleep(delay)
    return results
