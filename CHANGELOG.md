# Changelog

## [1.0.1] - 2025-06-07
### Fixed
- Renamed PyPI package to `biofetch-cli` (name `biofetch` was taken)
- Fixed UniProt `--info` flag metadata parsing
- Fixed PDB polymer chain count display

## [1.0.0] - 2025-06-07
### Added
- Initial release
- `fetch` command — NCBI, UniProt, PDB by accession ID
- `search` command — full-text search across all three databases
- `info` command — rich metadata panels without downloading sequences
- `batch` command — bulk fetch with progress bar and rate limiting
- `cache` subcommands — stats, list, clear, delete
- Local disk cache with 7-day TTL via diskcache
- Multiple output formats: FASTA, GenBank, JSON, XML, PDB, mmCIF, TSV
- 34 unit tests with mocked API responses
- Cross-platform: Windows and Linux
