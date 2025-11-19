# Microservices Version Sync Scripts

This directory contains Python scripts for synchronizing microservice versions between Helm charts and the AppState production repository.

## Scripts Overview

### 1. `extract_services.py`
Extracts microservices and their versions from Helm values files.

**Usage:**
```bash
python3 extract_services.py [options]
```

**Options:**
- `--core-services`: Path to frontegg-core-services values.yaml (default: `charts/frontegg-core-services/values.yaml`)
- `--dashboard`: Path to frontegg-dashboard values.yaml (default: `charts/frontegg-dashboard/values.yaml`)
- `--output-dir`: Output directory for JSON files (default: `.`)
- `--verbose, -v`: Verbose output

**Output files:**
- `core_services.json`: Services from frontegg-core-services
- `dashboard_services.json`: Services from frontegg-dashboard  
- `all_services.json`: Combined services list

### 2. `query_appstate.py`
Queries the AppState repository for production versions of microservices.

**Usage:**
```bash
export GITHUB_TOKEN="your_token_here"
python3 query_appstate.py [options]
```

**Options:**
- `--services-file`: JSON file containing services to query (default: `all_services.json`)
- `--output`: Output file for AppState versions (default: `appstate_versions.json`)
- `--token`: GitHub token (can also use GITHUB_TOKEN env var)
- `--repo`: AppState repository (default: `frontegg/AppState`)
- `--verbose, -v`: Verbose output

**Output:**
- `appstate_versions.json`: AppState production versions for each service

### 3. `compare_versions.py`
Compares Helm versions with AppState production versions and generates a summary.

**Usage:**
```bash
python3 compare_versions.py [options]
```

**Options:**
- `--services-file`: JSON file containing services (default: `all_services.json`)
- `--appstate-file`: JSON file containing AppState versions (default: `appstate_versions.json`)
- `--output`: Output file for comparison results (default: `comparison_results.json`)
- `--summary-file`: Optional file to save markdown summary
- `--verbose, -v`: Verbose output

**Output:**
- `comparison_results.json`: Detailed comparison results
- `summary.md`: Markdown summary (if --summary-file specified)

### 4. `update_values.py`
Updates Helm values files with new appVersion values.

**Usage:**
```bash
python3 update_values.py [options]
```

**Options:**
- `--comparison-file`: JSON file containing comparison results (default: `comparison_results.json`)
- `--core-services-values`: Path to frontegg-core-services values.yaml (default: `charts/frontegg-core-services/values.yaml`)
- `--dashboard-values`: Path to frontegg-dashboard values.yaml (default: `charts/frontegg-dashboard/values.yaml`)
- `--dry-run`: Show what would be updated without making changes
- `--verbose, -v`: Verbose output

### 5. `test_local.py`
Test script to run the complete microservices version sync locally.

**Usage:**
```bash
export GITHUB_TOKEN="your_token_here"
python3 test_local.py [options]
```

**Options:**
- `--github-token`: GitHub token for AppState queries
- `--dry-run`: Run in dry-run mode (no actual updates)
- `--verbose, -v`: Verbose output
- `--skip-appstate`: Skip AppState queries (for testing extraction only)

## Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### Test Locally (Extraction Only)
```bash
python3 scripts/test_local.py --skip-appstate --verbose
```

### Full Local Test (Requires GitHub Token)
```bash
export GITHUB_TOKEN="your_github_token"
python3 scripts/test_local.py --dry-run --verbose
```

### Run Individual Steps
```bash
# 1. Extract services
python3 scripts/extract_services.py --verbose

# 2. Query AppState (requires GITHUB_TOKEN)
python3 scripts/query_appstate.py --verbose

# 3. Compare versions
python3 scripts/compare_versions.py --verbose --summary-file summary.md

# 4. Update values (dry-run first)
python3 scripts/update_values.py --dry-run --verbose

# 5. Apply updates
python3 scripts/update_values.py --verbose
```

## Output Files

All scripts create output files in the current directory (or specified output directory):

- `core_services.json`: Core services extracted from values
- `dashboard_services.json`: Dashboard services extracted from values
- `all_services.json`: Combined services list
- `appstate_versions.json`: AppState production versions
- `comparison_results.json`: Version comparison results
- `summary.md`: Human-readable summary (optional)

## GitHub Actions Integration

These scripts are designed to work both locally and in GitHub Actions. When running in GitHub Actions (detected by the `GITHUB_ACTIONS` environment variable), they output additional metadata for workflow integration.

## Error Handling

All scripts include comprehensive error handling and will exit with non-zero codes on failure. Use `--verbose` for detailed error information.

## Supported Service Patterns

The scripts automatically detect services in the Helm values files based on:

- Presence of `appVersion` field
- Presence of `name` field  
- Valid service structure

For AppState queries, the scripts use the correct repository structure:
- `applications/{service-name}/production-global/values.yaml`
- `applications/{service-name}/production-global/values.yml` (fallback for .yml extension)

## Contributing

When modifying these scripts:

1. Test locally first using `test_local.py`
2. Ensure error handling is maintained
3. Update this README if adding new options
4. Test both verbose and quiet modes
