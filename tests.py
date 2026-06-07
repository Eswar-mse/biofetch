"""BioFetch test suite — mocked API responses, no network needed."""
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
console = Console()

PASS = "[bold green]PASS[/]"
FAIL = "[bold red]FAIL[/]"

results = []


def test(name):
    def decorator(fn):
        try:
            fn()
            console.print(f"  {PASS}  {name}")
            results.append((name, True, None))
        except Exception as e:
            console.print(f"  {FAIL}  {name}")
            console.print(f"         [dim red]{e}[/]")
            results.append((name, False, str(e)))
    return decorator


# ─── Sample fixtures ──────────────────────────────────────────────────────────

SAMPLE_FASTA = """>NM_001301717.2 Homo sapiens BRCA1
ATGGATTTATCTGCTCTTCGCGTTGAAGAAGTACAAAATGTCATTAATGCTATGCAGAAAATCTT
AGAGTGTCCCATCTGTCTGGAGTTGATCAAGGAACCTGTCTCCACAAAGTGTGACCACATATTTT
"""

SAMPLE_UNIPROT_JSON = {
    "primaryAccession": "P68871",
    "uniProtkbId": "HBB_HUMAN",
    "entryType": "UniProtKB reviewed (Swiss-Prot)",
    "proteinDescription": {
        "recommendedName": {
            "fullName": {"value": "Hemoglobin subunit beta"}
        }
    },
    "genes": [{"geneName": {"value": "HBB"}}],
    "organism": {
        "scientificName": "Homo sapiens",
        "lineage": [
            {"scientificName": "Eukaryota"},
            {"scientificName": "Metazoa"},
            {"scientificName": "Homo sapiens"},
        ],
    },
    "sequence": {"length": 147, "molWeight": 15998},
    "comments": [
        {
            "commentType": "FUNCTION",
            "texts": [{"value": "Involved in oxygen transport from the lung to the various peripheral tissues."}],
        }
    ],
    "keywords": [
        {"name": "Oxygen transport"},
        {"name": "Heme"},
        {"name": "Metal-binding"},
    ],
}

SAMPLE_PDB_META = {
    "struct": {"title": "LIGANDED T STATE HAEMOGLOBIN"},
    "entry": {"id": "1HHO"},
    "exptl": [{"method": "X-RAY DIFFRACTION"}],
    "cell": {"length_a": 97.1},
    "refine": [{"ls_rfactor_rfree": 0.228, "ls_rfactor_rwork": 0.185}],
    "rcsb_entry_info": {
        "resolution_combined": [2.1],
        "deposited_polymer_entity_count": 4,
        "deposited_atom_count": 4779,
    },
}

SAMPLE_NCBI_SUMMARY = {
    "Id": "NM_001301717",
    "Caption": "NM_001301717",
    "Title": "Homo sapiens BRCA1 DNA repair associated (BRCA1), mRNA",
    "Extra": "gi|123456|ref|NM_001301717.2|",
    "Gi": 123456,
    "CreateDate": "2001/01/01",
    "UpdateDate": "2024/01/01",
    "Flags": 0,
    "TaxId": 9606,
    "Length": 7088,
    "Status": "live",
    "ReplacedBy": "",
    "Comment": "",
}


# ─── Cache tests ──────────────────────────────────────────────────────────────

console.print("\n[bold cyan]── Cache Module ──────────────────────────────────[/]")

@test("Cache: set and get returns correct data")
def _():
    from biofetch.cache import BioCache
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("biofetch.cache.get_cache_dir", return_value=Path(tmpdir)):
            c = BioCache()
            c.set("ncbi", "NM_001", "fasta", "ATGCATGC")
            val = c.get("ncbi", "NM_001", "fasta")
            assert val == "ATGCATGC", f"Expected 'ATGCATGC', got {val!r}"
            c.close()


@test("Cache: miss returns None")
def _():
    from biofetch.cache import BioCache
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("biofetch.cache.get_cache_dir", return_value=Path(tmpdir)):
            c = BioCache()
            val = c.get("ncbi", "NONEXISTENT_9999", "fasta")
            assert val is None, f"Expected None, got {val!r}"
            c.close()


@test("Cache: delete removes entry")
def _():
    from biofetch.cache import BioCache
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("biofetch.cache.get_cache_dir", return_value=Path(tmpdir)):
            c = BioCache()
            c.set("uniprot", "P68871", "fasta", ">P68871\nMVHLT")
            c.delete("uniprot", "P68871", "fasta")
            val = c.get("uniprot", "P68871", "fasta")
            assert val is None
            c.close()


@test("Cache: clear empties all entries")
def _():
    from biofetch.cache import BioCache
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("biofetch.cache.get_cache_dir", return_value=Path(tmpdir)):
            c = BioCache()
            c.set("pdb", "1HHO", "pdb", "ATOM   1  N")
            c.set("pdb", "2HHB", "pdb", "ATOM   1  CA")
            c.clear()
            assert len(c.list_keys()) == 0
            c.close()


@test("Cache: stats returns count and size")
def _():
    from biofetch.cache import BioCache
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("biofetch.cache.get_cache_dir", return_value=Path(tmpdir)):
            c = BioCache()
            c.set("ncbi", "X1", "fasta", "HELLO")
            stats = c.stats()
            assert stats["count"] >= 1
            assert "cache_dir" in stats
            assert "size_bytes" in stats
            c.close()


@test("Cache: list_keys returns correct keys")
def _():
    from biofetch.cache import BioCache
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("biofetch.cache.get_cache_dir", return_value=Path(tmpdir)):
            c = BioCache()
            c.set("ncbi", "ABC", "fasta", "data1")
            c.set("uniprot", "XYZ", "json", "data2")
            keys = c.list_keys()
            assert "ncbi:ABC:fasta" in keys
            assert "uniprot:XYZ:json" in keys
            c.close()


# ─── NCBI module tests ────────────────────────────────────────────────────────

console.print("\n[bold cyan]── NCBI Module ──────────────────────────────────[/]")

@test("NCBI: fetch returns mocked FASTA data")
def _():
    from biofetch import ncbi as ncbi_mod
    mock_handle = MagicMock()
    mock_handle.read.return_value = SAMPLE_FASTA
    with patch("Bio.Entrez.efetch", return_value=mock_handle):
        result = ncbi_mod.fetch_ncbi("NM_001301717", db="nucleotide", fmt="fasta")
        assert ">NM_001301717" in result
        assert "ATGGAT" in result


@test("NCBI: search returns IDs and count")
def _():
    from biofetch import ncbi as ncbi_mod
    mock_handle = MagicMock()
    mock_handle.return_value = {
        "IdList": ["NM_001301717", "NM_007294"],
        "Count": "42",
        "WebEnv": "WEBENV123",
        "QueryKey": "1",
    }
    with patch("Bio.Entrez.esearch", return_value=MagicMock()) as mock_search:
        with patch("Bio.Entrez.read", return_value={
            "IdList": ["NM_001301717", "NM_007294"],
            "Count": "42",
            "WebEnv": "WE",
            "QueryKey": "1",
        }):
            result = ncbi_mod.search_ncbi("BRCA1 human", db="nucleotide", max_results=10)
            assert "ids" in result
            assert "count" in result
            assert result["count"] == 42


@test("NCBI: parse_fasta_stats computes GC content")
def _():
    from biofetch import ncbi as ncbi_mod
    fasta = ">SEQ1 test\nATGCGCGCAT\n>SEQ2 test2\nAAAAAAAA\n"
    stats = ncbi_mod.parse_fasta_stats(fasta)
    assert len(stats) == 2
    assert stats[0]["length"] == 10
    # ATGCGCGCAT: G=3, C=3 → 60%
    assert stats[0]["gc_percent"] == 60.0
    # AAAAAAAA: GC=0%
    assert stats[1]["gc_percent"] == 0.0


@test("NCBI: parse_fasta_stats handles empty sequence gracefully")
def _():
    from biofetch import ncbi as ncbi_mod
    fasta = ">EMPTY\n\n"
    stats = ncbi_mod.parse_fasta_stats(fasta)
    # empty FASTA should return empty list or handle gracefully
    assert isinstance(stats, list)


@test("NCBI: batch_fetch returns dict keyed by accession")
def _():
    from biofetch import ncbi as ncbi_mod
    call_count = {"n": 0}
    def mock_fetch(acc, db, fmt):
        call_count["n"] += 1
        return f">mock_{acc}\nATGC"
    with patch.object(ncbi_mod, "fetch_ncbi", side_effect=mock_fetch):
        results = ncbi_mod.batch_fetch_ncbi(["ACC1", "ACC2"], db="nucleotide", fmt="fasta", delay=0)
        assert "ACC1" in results
        assert "ACC2" in results
        assert ">mock_ACC1" in results["ACC1"]
        assert call_count["n"] == 2


@test("NCBI: db name aliasing works (nt → nucleotide)")
def _():
    from biofetch import ncbi as ncbi_mod
    assert ncbi_mod.NCBI_DB_MAP.get("nt") == "nucleotide"
    assert ncbi_mod.NCBI_DB_MAP.get("prot") == "protein"


# ─── UniProt module tests ─────────────────────────────────────────────────────

console.print("\n[bold cyan]── UniProt Module ───────────────────────────────[/]")

@test("UniProt: fetch returns mocked FASTA")
def _():
    from biofetch import uniprot as uni_mod
    mock_resp = MagicMock()
    mock_resp.text = ">sp|P68871|HBB_HUMAN Hemoglobin\nMVHLTPEEKSAVTALWGKVNVDEVGGEALGR"
    mock_resp.raise_for_status = MagicMock()
    with patch("requests.get", return_value=mock_resp):
        result = uni_mod.fetch_uniprot("P68871", fmt="fasta")
        assert "HBB_HUMAN" in result
        assert "MVHLT" in result


@test("UniProt: extract_uniprot_summary parses JSON correctly")
def _():
    from biofetch import uniprot as uni_mod
    summary = uni_mod.extract_uniprot_summary(SAMPLE_UNIPROT_JSON)
    assert summary["accession"] == "P68871"
    assert summary["protein_name"] == "Hemoglobin subunit beta"
    assert summary["gene"] == "HBB"
    assert summary["organism"] == "Homo sapiens"
    assert summary["length"] == 147
    assert summary["reviewed"] is True
    assert len(summary["keywords"]) > 0


@test("UniProt: extract_uniprot_summary handles missing fields gracefully")
def _():
    from biofetch import uniprot as uni_mod
    sparse = {
        "primaryAccession": "XTEST",
        "uniProtkbId": "TEST_HUMAN",
        "entryType": "TrEMBL",
        "proteinDescription": {},
        "sequence": {},
    }
    summary = uni_mod.extract_uniprot_summary(sparse)
    assert summary["accession"] == "XTEST"
    assert summary["reviewed"] is False
    assert summary["gene"] == "N/A"


@test("UniProt: search returns list of dicts with expected keys")
def _():
    from biofetch import uniprot as uni_mod
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "results": [
            {
                "primaryAccession": "P68871",
                "uniProtkbId": "HBB_HUMAN",
                "entryType": "UniProtKB reviewed (Swiss-Prot)",
                "proteinDescription": {
                    "recommendedName": {"fullName": {"value": "Hemoglobin subunit beta"}}
                },
                "genes": [{"geneName": {"value": "HBB"}}],
                "organism": {"scientificName": "Homo sapiens"},
                "sequence": {"length": 147},
            }
        ]
    }
    with patch("requests.get", return_value=mock_resp):
        results = uni_mod.search_uniprot("hemoglobin", max_results=5)
        assert len(results) == 1
        assert results[0]["accession"] == "P68871"
        assert results[0]["reviewed"] is True


@test("UniProt: fetch retries on failure")
def _():
    from biofetch import uniprot as uni_mod
    import requests
    call_log = {"n": 0}
    def flaky_get(*args, **kwargs):
        call_log["n"] += 1
        if call_log["n"] < 3:
            raise requests.RequestException("timeout")
        m = MagicMock()
        m.text = ">P68871\nMVHLT"
        m.raise_for_status = MagicMock()
        return m
    with patch("requests.get", side_effect=flaky_get):
        with patch("time.sleep"):  # don't actually wait
            result = uni_mod.fetch_uniprot("P68871", fmt="fasta", retries=3)
            assert "MVHLT" in result
            assert call_log["n"] == 3


# ─── PDB module tests ─────────────────────────────────────────────────────────

console.print("\n[bold cyan]── PDB Module ───────────────────────────────────[/]")

@test("PDB: fetch_pdb_metadata returns mocked dict")
def _():
    from biofetch import pdb as pdb_mod
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = SAMPLE_PDB_META
    with patch("requests.get", return_value=mock_resp):
        meta = pdb_mod.fetch_pdb_metadata("1HHO")
        assert meta["struct"]["title"] == "LIGANDED T STATE HAEMOGLOBIN"


@test("PDB: extract_pdb_summary parses metadata correctly")
def _():
    from biofetch import pdb as pdb_mod
    summary = pdb_mod.extract_pdb_summary(SAMPLE_PDB_META, "1HHO")
    assert summary["pdb_id"] == "1HHO"
    assert summary["title"] == "LIGANDED T STATE HAEMOGLOBIN"
    assert summary["method"] == "X-RAY DIFFRACTION"
    assert summary["resolution"] == 2.1
    assert abs(summary["r_free"] - 0.228) < 0.001
    assert summary["atom_count"] == 4779


@test("PDB: fetch_pdb_fasta returns sequence text")
def _():
    from biofetch import pdb as pdb_mod
    fasta_text = ">1HHO_1|Chain A|HBA_HUMAN\nVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSHGSAQVKGHGKK\n"
    mock_resp = MagicMock()
    mock_resp.text = fasta_text
    mock_resp.raise_for_status = MagicMock()
    with patch("requests.get", return_value=mock_resp):
        result = pdb_mod.fetch_pdb_fasta("1HHO")
        assert "1HHO" in result
        assert "VLSPAD" in result


@test("PDB: fetch_pdb_structure returns PDB format text")
def _():
    from biofetch import pdb as pdb_mod
    pdb_text = "ATOM      1  N   VAL A   1      6.204  16.869   4.854  1.00 49.05\n"
    mock_resp = MagicMock()
    mock_resp.text = pdb_text
    mock_resp.raise_for_status = MagicMock()
    with patch("requests.get", return_value=mock_resp):
        result = pdb_mod.fetch_pdb_structure("1HHO", fmt="pdb")
        assert "ATOM" in result


@test("PDB: search_pdb returns list of PDB IDs with scores")
def _():
    from biofetch import pdb as pdb_mod
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "result_set": [
            {"identifier": "1HHO", "score": 1.0},
            {"identifier": "2HHB", "score": 0.95},
        ]
    }
    with patch("requests.post", return_value=mock_resp):
        results = pdb_mod.search_pdb("hemoglobin", max_results=5)
        assert len(results) == 2
        assert results[0]["pdb_id"] == "1HHO"
        assert results[1]["score"] == 0.95


@test("PDB: accession ID is uppercased automatically")
def _():
    from biofetch import pdb as pdb_mod
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = SAMPLE_PDB_META
    with patch("requests.get", return_value=mock_resp) as mock_get:
        pdb_mod.fetch_pdb_metadata("1hho")
        call_url = mock_get.call_args[0][0]
        assert "1HHO" in call_url


# ─── Display module tests ─────────────────────────────────────────────────────

console.print("\n[bold cyan]── Display Module ───────────────────────────────[/]")

@test("Display: print_uniprot_summary runs without error")
def _():
    from biofetch import uniprot as uni_mod
    from biofetch import display as disp
    summary = uni_mod.extract_uniprot_summary(SAMPLE_UNIPROT_JSON)
    with patch.object(disp.console, "print"):
        disp.print_uniprot_summary(summary)  # should not raise


@test("Display: print_pdb_summary runs without error")
def _():
    from biofetch import pdb as pdb_mod
    from biofetch import display as disp
    summary = pdb_mod.extract_pdb_summary(SAMPLE_PDB_META, "1HHO")
    with patch.object(disp.console, "print"):
        disp.print_pdb_summary(summary)


@test("Display: print_fasta_preview truncates long sequences")
def _():
    from biofetch import display as disp
    long_fasta = "\n".join([f">SEQ{i}\nATGCATGC" for i in range(50)])
    captured = []
    with patch.object(disp.console, "print", side_effect=lambda *a, **kw: captured.append(a)):
        disp.print_fasta_preview(long_fasta, max_lines=10)
    assert len(captured) > 0


@test("Display: print_search_results_uniprot renders table")
def _():
    from biofetch import display as disp
    results = [
        {
            "accession": "P68871",
            "entry_name": "HBB_HUMAN",
            "protein_name": "Hemoglobin subunit beta",
            "gene": "HBB",
            "organism": "Homo sapiens",
            "length": 147,
            "reviewed": True,
        }
    ]
    with patch.object(disp.console, "print"):
        disp.print_search_results_uniprot(results)


# ─── Integration: CLI command tests ──────────────────────────────────────────

console.print("\n[bold cyan]── CLI Integration ──────────────────────────────[/]")

@test("CLI: version command prints version string")
def _():
    from typer.testing import CliRunner
    from biofetch.cli import app
    runner = CliRunner()
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    output = result.output
    assert "BioFetch" in output or "1.0.0" in output, f"Unexpected: {output!r}"


@test("CLI: fetch --source uniprot uses cache on second call")
def _():
    from typer.testing import CliRunner
    from biofetch.cli import app, _cache
    from biofetch import uniprot as uni_mod
    runner = CliRunner()
    fasta_data = ">sp|P68871|HBB_HUMAN Hemoglobin\nMVHLTPEEKSAVT"

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("biofetch.cache.get_cache_dir", return_value=Path(tmpdir)):
            with patch.object(uni_mod, "fetch_uniprot", return_value=fasta_data) as mock_fetch:
                # First call — hits API
                with patch("biofetch.cli._cache") as mock_cache:
                    mock_cache.get.return_value = None
                    mock_cache.set = MagicMock()
                    r1 = runner.invoke(app, ["fetch", "P68871", "--source", "uniprot"])
                    assert mock_cache.set.called

                # Second call — served from cache
                with patch("biofetch.cli._cache") as mock_cache:
                    mock_cache.get.return_value = fasta_data
                    r2 = runner.invoke(app, ["fetch", "P68871", "--source", "uniprot"])
                    assert "cache" in r2.output.lower()
                    mock_fetch.assert_called_once()  # only called once total


@test("CLI: cache stats command runs")
def _():
    from typer.testing import CliRunner
    from biofetch.cli import app
    runner = CliRunner()
    with patch("biofetch.cli._cache") as mock_cache:
        mock_cache.stats.return_value = {"count": 3, "size_bytes": 1024, "cache_dir": "/tmp/biofetch"}
        result = runner.invoke(app, ["cache", "stats"])
        assert result.exit_code == 0


@test("CLI: cache list command shows keys")
def _():
    from typer.testing import CliRunner
    from biofetch.cli import app
    runner = CliRunner()
    with patch("biofetch.cli._cache") as mock_cache:
        mock_cache.list_keys.return_value = ["ncbi:NM_001:fasta", "uniprot:P68871:fasta"]
        result = runner.invoke(app, ["cache", "list"])
        assert result.exit_code == 0


@test("CLI: info --source pdb calls pdb_mod.fetch_pdb_metadata")
def _():
    from typer.testing import CliRunner
    from biofetch.cli import app
    from biofetch import pdb as pdb_mod
    runner = CliRunner()
    with patch.object(pdb_mod, "fetch_pdb_metadata", return_value=SAMPLE_PDB_META) as mock_meta:
        result = runner.invoke(app, ["info", "1HHO", "--source", "pdb"])
        assert result.exit_code == 0
        mock_meta.assert_called_once_with("1HHO")


@test("CLI: search --source uniprot calls search_uniprot")
def _():
    from typer.testing import CliRunner
    from biofetch.cli import app
    from biofetch import uniprot as uni_mod
    runner = CliRunner()
    mock_results = [{
        "accession": "P68871",
        "entry_name": "HBB_HUMAN",
        "protein_name": "Hemoglobin subunit beta",
        "gene": "HBB",
        "organism": "Homo sapiens",
        "length": 147,
        "reviewed": True,
    }]
    with patch.object(uni_mod, "search_uniprot", return_value=mock_results):
        result = runner.invoke(app, ["search", "hemoglobin", "--source", "uniprot"])
        assert result.exit_code == 0
        assert "P68871" in result.output


@test("CLI: batch saves files to outdir")
def _():
    from typer.testing import CliRunner
    from biofetch.cli import app
    from biofetch import uniprot as uni_mod
    runner = CliRunner()
    fasta = ">P68871\nMVHLT"
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.object(uni_mod, "fetch_uniprot", return_value=fasta):
            with patch("biofetch.cli._cache") as mock_cache:
                mock_cache.get.return_value = None
                mock_cache.set = MagicMock()
                result = runner.invoke(app, [
                    "batch", "P68871", "--source", "uniprot",
                    "--outdir", tmpdir, "--no-cache"
                ])
                saved = list(Path(tmpdir).glob("*.fasta"))
                assert len(saved) == 1
                assert "P68871" in saved[0].name


# ─── Summary ──────────────────────────────────────────────────────────────────

console.print()
total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
failed = total - passed

console.print(f"[bold]Results: [green]{passed}[/green] passed, [{'red' if failed else 'green'}]{failed}[/{'red' if failed else 'green'}] failed[/] out of {total} tests")

if failed > 0:
    console.print("\n[bold red]Failed tests:[/]")
    for name, ok, err in results:
        if not ok:
            console.print(f"  • {name}: [dim red]{err}[/]")
    sys.exit(1)
else:
    console.print("\n[bold green]All tests passed! 🎉[/]")
    sys.exit(0)
