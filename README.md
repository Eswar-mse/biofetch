# BioFetch 🧬

> Unified NCBI · UniProt · PDB CLI fetcher with local caching

BioFetch is a cross-platform Python CLI tool that lets you search, fetch, and save biological records from NCBI, UniProt, and RCSB PDB — all from your terminal, with smart local caching so you never hit the same API twice.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![PyPI](https://img.shields.io/pypi/v/biofetch-cli)](https://pypi.org/project/biofetch-cli/) 
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

---

## Features

- **Fetch** sequences and structures by accession from NCBI, UniProt, or PDB
- **Search** all three databases with ranked results tables
- **Info** panel — rich metadata without downloading the full file
- **Batch** download hundreds of records with rate limiting and progress bar
- **Local cache** — results stored on disk (7-day TTL by default), instant repeat lookups
- **Multiple formats** — FASTA, GenBank, JSON, XML, PDB, mmCIF, TSV
- **Beautiful terminal output** powered by Rich
- No conda, no virtual environments needed — pure pip

---

## Installation

```bash
pip install biofetch-cli
```

Or install from source:

```bash
git clone https://github.com/yourname/biofetch.git
cd biofetch
pip install -e .
```

---

## Quick Start

```bash
# Fetch a nucleotide sequence from NCBI
biofetch fetch NM_001301717 --source ncbi

# Fetch a UniProt protein entry with metadata info panel
biofetch fetch P68871 --source uniprot --info

# Fetch a PDB structure as a .pdb file
biofetch fetch 1HHO --source pdb --format pdb --output 1HHO.pdb

# Search UniProt for hemoglobin (Swiss-Prot reviewed only)
biofetch search "hemoglobin" --source uniprot --reviewed --limit 5

# Search NCBI nucleotide database
biofetch search "BRCA1 human mRNA" --source ncbi --db nucleotide --limit 10

# Search PDB for insulin structures
biofetch search "insulin" --source pdb --limit 5

# Get rich metadata for a UniProt entry
biofetch info P68871 --source uniprot

# Get PDB entry summary
biofetch info 1HHO --source pdb

# Batch fetch multiple accessions
biofetch batch P68871 P69905 P68873 --source uniprot --outdir ./sequences

# Batch fetch NCBI records
biofetch batch NM_001301717 NM_000546 --source ncbi --db nucleotide --outdir ./data
```

---

## Commands

| Command | Description |
|---------|-------------|
| `biofetch fetch <ID>` | Fetch a single record |
| `biofetch search <query>` | Search a database |
| `biofetch info <ID>` | Show metadata summary |
| `biofetch batch <IDs...>` | Batch fetch and save |
| `biofetch cache stats` | Show cache size and count |
| `biofetch cache list` | List all cached keys |
| `biofetch cache clear` | Clear the entire cache |
| `biofetch cache delete <ID>` | Remove a specific cached entry |
| `biofetch version` | Print version |

---

## Fetch Options

| Flag | Description |
|------|-------------|
| `--source` / `-s` | `ncbi`, `uniprot`, or `pdb` |
| `--format` / `-f` | `fasta`, `genbank`, `json`, `xml`, `pdb`, `cif`, `tsv` |
| `--db` | NCBI database: `nucleotide`, `protein`, `gene`, `pubmed` |
| `--output` / `-o` | Save to file path |
| `--info` / `-i` | Show metadata panel |
| `--no-preview` | Skip terminal sequence preview |
| `--no-cache` | Force fresh API request |

---

## Cache

BioFetch caches all responses locally:

- **Windows**: `%LOCALAPPDATA%\biofetch\`
- **Linux/Mac**: `~/.cache/biofetch/`

Default TTL is **7 days**. Manage cache with the `biofetch cache` subcommands.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `biopython` | NCBI Entrez, sequence parsing |
| `requests` | UniProt & PDB REST APIs |
| `diskcache` | Local disk-based caching |
| `rich` | Terminal formatting & tables |
| `typer` | CLI framework |

All installable with `pip` — no conda, no virtual environment required.

---

## License

MIT

   Code written, developed and deployed by Sri Venkata Satya Sai Eswar M
