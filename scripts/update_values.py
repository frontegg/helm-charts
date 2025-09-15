#!/usr/bin/env python3
"""
Update Helm values files with new appVersion values.
"""

import json
import yaml
import sys
import argparse
from pathlib import Path


def update_values_file(file_path, service_key, new_version, dry_run=False):
    """Update appVersion in values file"""
    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        return False
    
    # Read the file
    with open(file_path, 'r') as f:
        values = yaml.safe_load(f)
    
    if service_key in values and 'appVersion' in values[service_key]:
        old_version = values[service_key]['appVersion']
        
        if old_version == new_version:
            print(f"  {service_key}: Already up to date ({new_version})")
            return False
        
        if dry_run:
            print(f"  {service_key}: Would update {old_version} → {new_version}")
            return True
        
        values[service_key]['appVersion'] = new_version
        
        # Write back to file
        with open(file_path, 'w') as f:
            yaml.dump(values, f, default_flow_style=False, sort_keys=False)
        
        print(f"  {service_key}: Updated {old_version} → {new_version}")
        return True
    else:
        print(f"Warning: Could not find {service_key}.appVersion in {file_path}")
        return False


def find_service_key_in_values(file_path, service_name):
    """Find the service key by matching service name in values file"""
    with open(file_path, 'r') as f:
        values = yaml.safe_load(f)
    
    for key, value in values.items():
        if isinstance(value, dict) and value.get('name') == service_name:
            return key
    
    return None


def main():
    parser = argparse.ArgumentParser(description='Update Helm values files with new versions')
    parser.add_argument('--comparison-file', 
                       default='comparison_results.json',
                       help='JSON file containing comparison results')
    parser.add_argument('--core-services-values', 
                       default='charts/frontegg-core-services/values.yaml',
                       help='Path to frontegg-core-services values.yaml')
    parser.add_argument('--dashboard-values', 
                       default='charts/frontegg-dashboard/values.yaml',
                       help='Path to frontegg-dashboard values.yaml')
    parser.add_argument('--dry-run', 
                       action='store_true',
                       help='Show what would be updated without making changes')
    parser.add_argument('--verbose', '-v', 
                       action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        # Load comparison results
        if not Path(args.comparison_file).exists():
            print(f"Error: Comparison file not found: {args.comparison_file}", file=sys.stderr)
            return 1
        
        with open(args.comparison_file, 'r') as f:
            results = json.load(f)
        
        updates_needed = results.get('updates_needed', [])
        
        if not updates_needed:
            print("No updates needed")
            return 0
        
        if args.dry_run:
            print("DRY RUN MODE - No files will be modified")
            print()
        
        updated_files = set()
        successful_updates = 0
        
        print(f"Processing {len(updates_needed)} updates...")
        print()
        
        for update in updates_needed:
            service_name = update['service']
            chart = update['chart']
            new_version = update['appstate_version']
            
            print(f"Updating {service_name} ({chart}):")
            
            # Determine file path and service key
            if chart == 'frontegg-core-services':
                file_path = args.core_services_values
                
                # Find the service key by loading the file and matching service name
                service_key = find_service_key_in_values(file_path, service_name)
                
                if not service_key:
                    print(f"  Warning: Could not find service key for {service_name}")
                    continue
                    
            elif chart == 'frontegg-dashboard':
                file_path = args.dashboard_values
                service_key = 'dashboard'
            else:
                print(f"  Warning: Unknown chart {chart}")
                continue
            
            # Update the file
            if update_values_file(file_path, service_key, new_version, args.dry_run):
                updated_files.add(file_path)
                successful_updates += 1
        
        print()
        print(f"Summary:")
        print(f"  • Successful updates: {successful_updates}")
        print(f"  • Files modified: {len(updated_files)}")
        
        if updated_files:
            print(f"  • Updated files:")
            for file_path in sorted(updated_files):
                print(f"    - {file_path}")
        
        if args.dry_run:
            print("\nTo apply these changes, run without --dry-run")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
