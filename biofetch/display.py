"""Rich terminal display helpers for BioFetch."""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.syntax import Syntax
from rich import box
from typing import Optional
import contextlib

console = Console()


def spinner(message: str):
    """Context manager: show a spinner while work happens."""
    return Progress(
        SpinnerColumn(spinner_name="dots", style="bold cyan"),
        TextColumn("[cyan]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    )


def print_header():
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]BioFetch[/] [dim]v1.0.0[/]  •  [dim]NCBI · UniProt · PDB[/]",
            border_style="cyan",
            padding=(0, 2),
        )
    )
    console.print()


def print_success(msg: str):
    console.print(f"[bold green]✓[/]  {msg}")


def print_error(msg: str):
    console.print(f"[bold red]✗[/]  {msg}")


def print_warning(msg: str):
    console.print(f"[bold yellow]⚠[/]  {msg}")


def print_info(msg: str):
    console.print(f"[bold cyan]→[/]  {msg}")


def print_fasta_preview(fasta_text: str, max_lines: int = 20):
    """Print a syntax-highlighted FASTA preview."""
    lines = fasta_text.strip().splitlines()
    preview = "\n".join(lines[:max_lines])
    if len(lines) > max_lines:
        preview += f"\n... [{len(lines) - max_lines} more lines]"
    syntax = Syntax(preview, "text", theme="monokai", line_numbers=False, word_wrap=True)
    console.print(Panel(syntax, title="[bold]Sequence Preview[/]", border_style="dim"))


def print_ncbi_summary(record: dict):
    """Display NCBI DocSum metadata as a rich table."""
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column("Field", style="bold cyan", min_width=18)
    table.add_column("Value", style="white")

    skip = {"Item"}
    for k, v in record.items():
        if k in skip:
            continue
        val = str(v)
        if len(val) > 120:
            val = val[:117] + "..."
        table.add_row(k, val)

    console.print(Panel(table, title="[bold cyan]NCBI Record Info[/]", border_style="cyan"))


def print_uniprot_summary(summary: dict):
    """Display UniProt metadata summary."""
    reviewed_badge = "[bold green]✓ Swiss-Prot[/]" if summary.get("reviewed") else "[dim]TrEMBL[/]"

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column("Field", style="bold cyan", min_width=18)
    table.add_column("Value", style="white")

    table.add_row("Accession", f"[bold]{summary['accession']}[/]")
    table.add_row("Entry Name", summary.get("entry_name", "N/A"))
    table.add_row("Protein Name", summary.get("protein_name", "N/A"))
    table.add_row("Gene", summary.get("gene", "N/A"))
    table.add_row("Organism", f"[italic]{summary.get('organism', 'N/A')}[/]")
    table.add_row("Taxonomy", f"[dim]{summary.get('taxonomy', 'N/A')}[/]")
    table.add_row("Length", f"{summary.get('length', 0):,} aa")
    table.add_row("Mass", f"{summary.get('mass', 0):,} Da" if summary.get("mass") else "N/A")
    table.add_row("Reviewed", reviewed_badge)
    table.add_row("Keywords", ", ".join(summary.get("keywords", [])) or "N/A")
    if summary.get("function") and summary["function"] != "N/A":
        func = summary["function"]
        table.add_row("Function", f"[dim]{func}[/]")

    console.print(Panel(table, title="[bold cyan]UniProt Summary[/]", border_style="cyan"))


def print_pdb_summary(summary: dict):
    """Display PDB metadata summary."""
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column("Field", style="bold cyan", min_width=18)
    table.add_column("Value", style="white")

    res = summary.get("resolution")
    r_free = summary.get("r_free")

    table.add_row("PDB ID", f"[bold]{summary['pdb_id']}[/]")
    table.add_row("Title", summary.get("title", "N/A"))
    table.add_row("Method", summary.get("method", "N/A"))
    table.add_row("Resolution", f"{res} Å" if res else "N/A")
    table.add_row("R-free", f"{r_free:.3f}" if r_free else "N/A")
    table.add_row("R-work", f"{summary.get('r_work'):.3f}" if summary.get("r_work") else "N/A")
    table.add_row("Polymer chains", str(summary.get("polymer_count", "N/A")))
    table.add_row("Atom count", f"{summary.get('atom_count', 0):,}")

    console.print(Panel(table, title="[bold cyan]PDB Entry Summary[/]", border_style="cyan"))


def print_search_results_ncbi(results: dict, db: str):
    """Display NCBI search result IDs."""
    ids = results.get("ids", [])
    total = results.get("count", 0)
    console.print(f"\n[bold cyan]Found {total:,} total results[/] — showing top {len(ids)}\n")

    table = Table(box=box.SIMPLE_HEAD, show_header=True, padding=(0, 1))
    table.add_column("#", style="dim", width=4)
    table.add_column("Accession / ID", style="bold white")
    table.add_column("Database", style="cyan")

    for i, acc_id in enumerate(ids, 1):
        table.add_row(str(i), acc_id, db)

    console.print(table)


def print_search_results_uniprot(results: list):
    """Display UniProt search results as a table."""
    console.print(f"\n[bold cyan]UniProt Search Results[/] — {len(results)} hits\n")

    table = Table(box=box.SIMPLE_HEAD, show_header=True, padding=(0, 1))
    table.add_column("#", style="dim", width=4)
    table.add_column("Accession", style="bold white", width=12)
    table.add_column("Protein Name", style="white")
    table.add_column("Gene", style="cyan", width=12)
    table.add_column("Organism", style="italic dim")
    table.add_column("Length", style="green", width=8, justify="right")
    table.add_column("Reviewed", style="yellow", width=10)

    for i, r in enumerate(results, 1):
        reviewed = "[green]✓[/]" if r.get("reviewed") else "[dim]—[/]"
        table.add_row(
            str(i),
            r["accession"],
            r["protein_name"][:50] + "…" if len(r.get("protein_name", "")) > 50 else r.get("protein_name", ""),
            r.get("gene", ""),
            r.get("organism", "")[:30],
            f"{r.get('length', 0):,}",
            reviewed,
        )

    console.print(table)


def print_search_results_pdb(results: list):
    """Display PDB search results."""
    console.print(f"\n[bold cyan]PDB Search Results[/] — {len(results)} hits\n")
    table = Table(box=box.SIMPLE_HEAD, show_header=True, padding=(0, 1))
    table.add_column("#", style="dim", width=4)
    table.add_column("PDB ID", style="bold white", width=8)
    table.add_column("Score", style="green", width=10)

    for i, r in enumerate(results, 1):
        table.add_row(str(i), r["pdb_id"], str(r["score"]))
    console.print(table)


def print_cache_stats(stats: dict):
    """Display cache statistics."""
    size_kb = stats["size_bytes"] / 1024
    size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column("Field", style="bold cyan", min_width=18)
    table.add_column("Value", style="white")
    table.add_row("Cached entries", str(stats["count"]))
    table.add_row("Cache size", size_str)
    table.add_row("Cache location", f"[dim]{stats['cache_dir']}[/]")

    console.print(Panel(table, title="[bold cyan]Cache Stats[/]", border_style="cyan"))


def print_batch_summary(results: dict):
    """Display batch fetch results table."""
    table = Table(box=box.SIMPLE_HEAD, show_header=True, padding=(0, 1))
    table.add_column("Accession", style="bold white")
    table.add_column("Status", style="white")
    table.add_column("Size", style="cyan", justify="right")

    for acc, data in results.items():
        if data.startswith("ERROR:"):
            status = "[bold red]Failed[/]"
            size = "—"
        else:
            status = "[bold green]OK[/]"
            size = f"{len(data):,} bytes"
        table.add_row(acc, status, size)

    console.print(Panel(table, title="[bold cyan]Batch Fetch Results[/]", border_style="cyan"))
