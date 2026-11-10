#!/usr/bin/env python3
"""
Generate a summary table for the GitHub Actions job summary.
This script reads comparison results and generates a formatted table.
"""

import json
import sys
import argparse
from pathlib import Path


def generate_table(comparison_file, dry_run=False):
    """Generate a markdown table from comparison results"""
    
    try:
        with open(comparison_file, 'r') as f:
            results = json.load(f)
        
        # Print table header
        print('| Service | Chart | Original Version | Updated Version | Status |')
        print('|---------|-------|------------------|-----------------|--------|')
        
        # Print services that need updates
        updates_needed = results.get('updates_needed', [])
        for update in updates_needed:
            service = update.get('service', 'Unknown')
            chart = update.get('chart', 'Unknown')
            helm_ver = update.get('helm_version', 'Unknown')
            appstate_ver = update.get('appstate_version', 'Unknown')
            status = '🔄 Would update' if dry_run else '✅ Updated'
            print(f'| {service} | {chart} | `{helm_ver}` | `{appstate_ver}` | {status} |')
        
        # Print up-to-date services
        up_to_date = results.get('up_to_date', [])
        for service_info in up_to_date:
            service = service_info.get('service', 'Unknown')
            chart = service_info.get('chart', 'Unknown')
            version = service_info.get('version', 'Unknown')
            print(f'| {service} | {chart} | `{version}` | `{version}` | ✅ Up to date |')
        
        if not updates_needed and not up_to_date:
            print('| No data | - | - | - | ❌ No comparison data available |')
            
        return 0
        
    except FileNotFoundError:
        print('| Error | - | - | - | ❌ Comparison results file not found |')
        return 1
    except json.JSONDecodeError as e:
        print('| Error | - | - | - | ❌ Invalid JSON in comparison results |')
        print(f'JSON Error: {str(e)}', file=sys.stderr)
        return 1
    except Exception as e:
        print('| Error | - | - | - | ❌ Failed to parse comparison data |')
        print(f'Error details: {str(e)}', file=sys.stderr)
        return 1


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Generate summary table from comparison results')
    parser.add_argument('--comparison-file', 
                       default='comparison_results.json',
                       help='Path to comparison results JSON file')
    parser.add_argument('--dry-run', 
                       action='store_true',
                       help='Generate table for dry-run mode')
    
    args = parser.parse_args()
    
    return generate_table(args.comparison_file, args.dry_run)


if __name__ == '__main__':
    sys.exit(main())
