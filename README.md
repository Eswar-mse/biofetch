<div align="center">

# 🧬 BioFetch

**Unified NCBI · UniProt · PDB CLI fetcher with local caching**

[![Tests](https://github.com/Eswar-mse/biofetch/actions/workflows/ci.yml/badge.svg)](https://github.com/Eswar-mse/biofetch/actions)
[![PyPI](https://img.shields.io/pypi/v/biofetch-cli?color=blue)](https://pypi.org/project/biofetch-cli/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://pypi.org/project/biofetch-cli/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](#)

</div>

---

BioFetch is a cross-platform Python CLI tool that gives you instant access to **NCBI**, **UniProt**, and **RCSB PDB** — all from your terminal. Search, fetch, and save biological records by accession ID, with smart local caching so you never hit the same API twice.

No conda. No virtual environments. Just pip and go.

---

## ✨ Features

| | Feature | Description |
|---|---|---|
| 🔍 | **Search** | Query NCBI, UniProt, and PDB with ranked results |
| ⬇️ | **Fetch** | Download sequences and structures by accession ID |
| 📋 | **Info** | Rich metadata panels — no full download needed |
| 📦 | **Batch** | Bulk fetch hundreds of records with progress bar |
| ⚡ | **Cache** | 7-day local disk cache — instant repeat lookups |
| 🎨 | **Rich UI** | Beautiful terminal tables, spinners, and panels |
| 🔄 | **Formats** | FASTA · GenBank · JSON · XML · PDB · mmCIF · TSV |
| 🌍 | **Cross-platform** | Windows, Linux, macOS — pure pip |

---

## 🚀 Quick Start

```bash
# Fetch a protein sequence from UniProt
biofetch fetch P68871 --source uniprot

# Fetch with full metadata panel
biofetch fetch P68871 --source uniprot --info

# Download a PDB structure file
biofetch fetch 1HHO --source pdb --format pdb --output 1HHO.pdb

# Fetch a gene from NCBI
biofetch fetch NM_007294 --source ncbi --db nucleotide

# Search UniProt (Swiss-Prot reviewed only)
biofetch search "hemoglobin" --source uniprot --reviewed --limit 5

# Search PDB for insulin structures
biofetch search "insulin" --source pdb --limit 5

# Search NCBI
biofetch search "BRCA1 human mRNA" --source ncbi --db nucleotide --limit 8

# Batch fetch and save to folder
biofetch batch P68871 P69905 P68873 --source uniprot --outdir ./sequences

# Cache management
biofetch cache stats
biofetch cache list
biofetch cache clear
```

---

## 📖 Commands

| Command | Description |
|---|---|
| `biofetch fetch <ID>` | Fetch a single record by accession |
| `biofetch search <query>` | Search a database |
| `biofetch info <ID>` | Rich metadata summary |
| `biofetch batch <IDs...>` | Bulk fetch and save |
| `biofetch cache stats` | Cache size and entry count |
| `biofetch cache list` | List all cached keys |
| `biofetch cache clear` | Wipe the cache |
| `biofetch cache delete <ID>` | Remove one cached entry |
| `biofetch version` | Print version |

---

## ⚙️ Fetch Options

| Flag | Description |
|---|---|
| `--source` / `-s` | `ncbi`, `uniprot`, or `pdb` |
| `--format` / `-f` | `fasta`, `genbank`, `json`, `xml`, `pdb`, `cif`, `tsv` |
| `--db` | NCBI database: `nucleotide`, `protein`, `gene`, `pubmed` |
| `--output` / `-o` | Save to file |
| `--info` / `-i` | Show metadata panel |
| `--no-preview` | Skip terminal preview |
| `--no-cache` | Force fresh API call |

---

## 💾 Cache

Results are cached locally for 7 days:

- **Linux/Mac**: `~/.cache/biofetch/`
- **Windows**: `%LOCALAPPDATA%\biofetch\`

```bash
biofetch cache stats   # see how much is cached
biofetch cache clear   # wipe everything
```

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `biopython` | NCBI Entrez, sequence parsing |
| `requests` | UniProt & PDB REST APIs |
| `diskcache` | Local disk-based caching |
| `rich` | Terminal formatting & tables |
| `typer` | CLI framework |

All pure pip — no conda, no virtualenv required.

---

## 🧪 Tests

```bash
git clone https://github.com/Eswar-mse/biofetch.git
cd biofetch
pip install -e .
python tests.py
```

34 tests, fully mocked — no network required to run the suite.

---

## 📄 License

MIT © [Eswar-mse](https://github.com/Eswar-mse)

---

<div align="center">

Built with 🧬 by [Sri Venkata Satya Sai Eswar M](https://github.com/Eswar-mse)

**[PyPI](https://pypi.org/project/biofetch-cli/) · [Issues](https://github.com/Eswar-mse/biofetch/issues) · [Changelog](CHANGELOG.md)**

</div>
