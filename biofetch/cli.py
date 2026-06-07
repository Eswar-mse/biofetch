"""BioFetch — CLI entry point built with Typer."""
import sys
import os
from pathlib import Path
from typing import Optional, List
from enum import Enum

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from biofetch.cache import BioCache
from biofetch import ncbi as ncbi_mod
from biofetch import uniprot as uniprot_mod
from biofetch import pdb as pdb_mod
from biofetch import display as disp

app = typer.Typer(
    name="biofetch",
    help="[bold cyan]BioFetch[/] — Unified NCBI · UniProt · PDB fetcher with local caching.",
    rich_markup_mode="rich",
    add_completion=False,
    no_args_is_help=True,
)

cache_app = typer.Typer(help="Manage the local cache.", no_args_is_help=True)
app.add_typer(cache_app, name="cache")

_cache = BioCache(ttl_days=7)


# ─── Enums ───────────────────────────────────────────────────────────────────

class Source(str, Enum):
    ncbi = "ncbi"
    uniprot = "uniprot"
    pdb = "pdb"


class NCBIDb(str, Enum):
    nucleotide = "nucleotide"
    protein = "protein"
    gene = "gene"
    pubmed = "pubmed"


class NCBIFormat(str, Enum):
    fasta = "fasta"
    genbank = "genbank"
    xml = "xml"
    text = "text"


class UniProtFormat(str, Enum):
    fasta = "fasta"
    json = "json"
    txt = "txt"
    xml = "xml"
    tsv = "tsv"


class PDBFormat(str, Enum):
    pdb = "pdb"
    cif = "cif"
    fasta = "fasta"


# ─── fetch command ────────────────────────────────────────────────────────────

@app.command("fetch")
def fetch(
    accession: str = typer.Argument(..., help="Accession ID (e.g. NM_001301717, P68871, 1HHO)"),
    source: Source = typer.Option(..., "--source", "-s", help="Database source"),
    fmt: str = typer.Option("fasta", "--format", "-f", help="Output format"),
    db: NCBIDb = typer.Option(NCBIDb.nucleotide, "--db", help="NCBI database (only for --source ncbi)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save to file instead of printing"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass cache and force fresh fetch"),
    info: bool = typer.Option(False, "--info", "-i", help="Show metadata summary alongside sequence"),
    preview: bool = typer.Option(True, "--preview/--no-preview", help="Print sequence preview in terminal"),
):
    """Fetch a single record by accession ID from NCBI, UniProt, or PDB."""
    disp.print_header()

    accession = accession.strip()
    cache_key_fmt = fmt

    # ── Cache check ──
    if not no_cache:
        cached = _cache.get(source.value, accession, cache_key_fmt)
        if cached:
            disp.print_success(f"[bold]{accession}[/] served from cache")
            _deliver(cached, output, preview, source, accession, fmt, info)
            return

    # ── Fetch ──
    data = None
    with Progress(
        SpinnerColumn(spinner_name="dots", style="bold cyan"),
        TextColumn(f"[cyan]Fetching [bold]{accession}[/] from {source.value.upper()}..."),
        TimeElapsedColumn(),
        transient=True,
    ) as progress:
        progress.add_task("fetch", total=None)
        try:
            if source == Source.ncbi:
                data = ncbi_mod.fetch_ncbi(accession, db=db.value, fmt=fmt)
            elif source == Source.uniprot:
                data = uniprot_mod.fetch_uniprot(accession, fmt=fmt)
            elif source == Source.pdb:
                if fmt == "fasta":
                    data = pdb_mod.fetch_pdb_fasta(accession)
                else:
                    data = pdb_mod.fetch_pdb_structure(accession, fmt=fmt)
        except Exception as e:
            disp.print_error(str(e))
            raise typer.Exit(1)

    if not data:
        disp.print_error(f"No data returned for {accession}")
        raise typer.Exit(1)

    _cache.set(source.value, accession, cache_key_fmt, data)
    disp.print_success(f"[bold]{accession}[/] fetched and cached")
    _deliver(data, output, preview, source, accession, fmt, info)


def _deliver(data: str, output, preview: bool, source, accession: str, fmt: str, info: bool):
    """Write to file or print to terminal."""
    if output:
        output.write_text(data, encoding="utf-8")
        disp.print_info(f"Saved to [bold]{output}[/] ({len(data):,} bytes)")
    else:
        if preview:
            disp.print_fasta_preview(data, max_lines=24)

    # ── Optional info panel ──
    if info:
        try:
            if source == Source.ncbi and fmt == "fasta":
                stats = ncbi_mod.parse_fasta_stats(data)
                if stats:
                    from rich.table import Table
                    from rich import box
                    t = Table(box=box.SIMPLE_HEAD)
                    t.add_column("ID")
                    t.add_column("Length", justify="right")
                    t.add_column("GC %", justify="right")
                    for s in stats:
                        t.add_row(s["id"], f"{s['length']:,}", f"{s['gc_percent']}%")
                    disp.console.print(t)
            elif source == Source.uniprot:
                meta = uniprot_mod.fetch_uniprot_metadata(accession)
                summary = uniprot_mod.extract_uniprot_summary(meta)
                disp.print_uniprot_summary(summary)
            elif source == Source.pdb:
                meta = pdb_mod.fetch_pdb_metadata(accession)
                summary = pdb_mod.extract_pdb_summary(meta, accession)
                disp.print_pdb_summary(summary)
        except Exception as e:
            disp.print_warning(f"Could not fetch metadata: {e}")


# ─── search command ───────────────────────────────────────────────────────────

@app.command("search")
def search(
    query: str = typer.Argument(..., help="Search query string"),
    source: Source = typer.Option(Source.ncbi, "--source", "-s", help="Database to search"),
    db: NCBIDb = typer.Option(NCBIDb.nucleotide, "--db", help="NCBI database (for --source ncbi)"),
    limit: int = typer.Option(10, "--limit", "-n", help="Max results to return"),
    reviewed: bool = typer.Option(False, "--reviewed", help="UniProt: only Swiss-Prot reviewed entries"),
):
    """Search NCBI, UniProt, or PDB and list matching accessions."""
    disp.print_header()

    with Progress(
        SpinnerColumn(spinner_name="dots", style="bold cyan"),
        TextColumn(f"[cyan]Searching {source.value.upper()} for [bold]{query!r}[/]..."),
        TimeElapsedColumn(),
        transient=True,
    ) as progress:
        progress.add_task("search", total=None)
        try:
            if source == Source.ncbi:
                results = ncbi_mod.search_ncbi(query, db=db.value, max_results=limit)
                disp.print_search_results_ncbi(results, db.value)
            elif source == Source.uniprot:
                results = uniprot_mod.search_uniprot(query, max_results=limit, reviewed=reviewed)
                disp.print_search_results_uniprot(results)
            elif source == Source.pdb:
                results = pdb_mod.search_pdb(query, max_results=limit)
                disp.print_search_results_pdb(results)
        except Exception as e:
            disp.print_error(str(e))
            raise typer.Exit(1)


# ─── info command ─────────────────────────────────────────────────────────────

@app.command("info")
def info_cmd(
    accession: str = typer.Argument(..., help="Accession ID"),
    source: Source = typer.Option(..., "--source", "-s", help="Database source"),
    db: NCBIDb = typer.Option(NCBIDb.nucleotide, "--db", help="NCBI database"),
):
    """Fetch and display a rich metadata summary without downloading the full sequence."""
    disp.print_header()
    accession = accession.strip()

    with Progress(
        SpinnerColumn(spinner_name="dots", style="bold cyan"),
        TextColumn(f"[cyan]Loading info for [bold]{accession}[/]..."),
        TimeElapsedColumn(),
        transient=True,
    ) as progress:
        progress.add_task("info", total=None)
        try:
            if source == Source.ncbi:
                record = ncbi_mod.fetch_ncbi_summary(accession, db=db.value)
                if record:
                    disp.print_ncbi_summary(record)
                else:
                    disp.print_error("No summary found.")
            elif source == Source.uniprot:
                meta = uniprot_mod.fetch_uniprot_metadata(accession)
                summary = uniprot_mod.extract_uniprot_summary(meta)
                disp.print_uniprot_summary(summary)
            elif source == Source.pdb:
                meta = pdb_mod.fetch_pdb_metadata(accession)
                summary = pdb_mod.extract_pdb_summary(meta, accession)
                disp.print_pdb_summary(summary)
        except Exception as e:
            disp.print_error(str(e))
            raise typer.Exit(1)


# ─── batch command ────────────────────────────────────────────────────────────

@app.command("batch")
def batch(
    accessions: List[str] = typer.Argument(..., help="Space-separated accession IDs"),
    source: Source = typer.Option(..., "--source", "-s", help="Database source"),
    fmt: str = typer.Option("fasta", "--format", "-f", help="Output format"),
    db: NCBIDb = typer.Option(NCBIDb.nucleotide, "--db", help="NCBI database"),
    outdir: Path = typer.Option(Path("."), "--outdir", "-d", help="Directory to save files"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass cache"),
):
    """Batch fetch multiple accession IDs and save each to a file."""
    disp.print_header()
    outdir.mkdir(parents=True, exist_ok=True)

    results = {}
    with Progress(
        SpinnerColumn(spinner_name="dots", style="bold cyan"),
        TextColumn("[cyan]{task.description}"),
        TimeElapsedColumn(),
        transient=False,
    ) as progress:
        task = progress.add_task(f"Fetching {len(accessions)} records...", total=len(accessions))

        for acc in accessions:
            acc = acc.strip()
            progress.update(task, description=f"[cyan]Fetching [bold]{acc}[/]...")

            if not no_cache:
                cached = _cache.get(source.value, acc, fmt)
                if cached:
                    results[acc] = cached
                    _save_record(cached, acc, fmt, outdir)
                    progress.advance(task)
                    continue

            try:
                if source == Source.ncbi:
                    data = ncbi_mod.fetch_ncbi(acc, db=db.value, fmt=fmt)
                elif source == Source.uniprot:
                    data = uniprot_mod.fetch_uniprot(acc, fmt=fmt)
                elif source == Source.pdb:
                    data = pdb_mod.fetch_pdb_fasta(acc) if fmt == "fasta" else pdb_mod.fetch_pdb_structure(acc, fmt=fmt)

                _cache.set(source.value, acc, fmt, data)
                results[acc] = data
                _save_record(data, acc, fmt, outdir)
            except Exception as e:
                results[acc] = f"ERROR: {e}"

            progress.advance(task)

    disp.print_batch_summary(results)
    disp.print_info(f"Files saved to [bold]{outdir.resolve()}[/]")


def _save_record(data: str, accession: str, fmt: str, outdir: Path):
    ext_map = {"fasta": "fasta", "genbank": "gb", "gb": "gb", "json": "json",
               "xml": "xml", "txt": "txt", "pdb": "pdb", "cif": "cif"}
    ext = ext_map.get(fmt, fmt)
    fname = outdir / f"{accession}.{ext}"
    fname.write_text(data, encoding="utf-8")


# ─── cache subcommands ────────────────────────────────────────────────────────

@cache_app.command("stats")
def cache_stats():
    """Show cache size and entry count."""
    disp.print_header()
    stats = _cache.stats()
    disp.print_cache_stats(stats)


@cache_app.command("list")
def cache_list():
    """List all cached keys."""
    disp.print_header()
    keys = _cache.list_keys()
    if not keys:
        disp.print_info("Cache is empty.")
        return
    disp.console.print(f"\n[bold cyan]{len(keys)} cached entries:[/]\n")
    for k in keys:
        disp.console.print(f"  [dim]→[/] {k}")


@cache_app.command("clear")
def cache_clear(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """Clear all cached data."""
    disp.print_header()
    if not force:
        confirm = typer.confirm("⚠  This will delete all cached records. Continue?")
        if not confirm:
            disp.print_info("Aborted.")
            return
    _cache.clear()
    disp.print_success("Cache cleared.")


@cache_app.command("delete")
def cache_delete(
    accession: str = typer.Argument(..., help="Accession ID to remove from cache"),
    source: Source = typer.Option(..., "--source", "-s"),
    fmt: str = typer.Option("fasta", "--format", "-f"),
):
    """Delete a specific cached entry."""
    disp.print_header()
    deleted = _cache.delete(source.value, accession, fmt)
    if deleted:
        disp.print_success(f"Deleted cache entry: {source.value}:{accession}:{fmt}")
    else:
        disp.print_warning(f"Entry not found in cache: {source.value}:{accession}:{fmt}")


# ─── version command ──────────────────────────────────────────────────────────

@app.command("version")
def version():
    """Print BioFetch version."""
    from biofetch import __version__
    disp.console.print(f"[bold cyan]BioFetch[/] v{__version__}")


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    app()


if __name__ == "__main__":
    main()
