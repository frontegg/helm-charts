#!/usr/bin/env python3
"""
Test script to run the microservices version sync locally.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def setup_virtual_environment():
    """Set up virtual environment if not already in one"""
    if os.environ.get('VIRTUAL_ENV'):
        print("✅ Already in virtual environment")
        return True
    
    venv_path = Path('scripts/venv')
    if not venv_path.exists():
        print("🔧 Creating virtual environment...")
        try:
            subprocess.run([sys.executable, '-m', 'venv', str(venv_path)], check=True)
            print("✅ Virtual environment created")
        except subprocess.CalledProcessError:
            print("❌ Failed to create virtual environment")
            return False
    
    # Install dependencies in the virtual environment
    pip_path = venv_path / 'bin' / 'pip'
    if not pip_path.exists():
        pip_path = venv_path / 'Scripts' / 'pip.exe'  # Windows
    
    if pip_path.exists():
        print("📦 Installing dependencies in virtual environment...")
        try:
            subprocess.run([str(pip_path), 'install', '-r', 'scripts/requirements.txt'], check=True)
            print("✅ Dependencies installed")
            
            # Update Python path to use venv
            python_path = venv_path / 'bin' / 'python3'
            if not python_path.exists():
                python_path = venv_path / 'Scripts' / 'python.exe'  # Windows
            
            os.environ['PYTHON_PATH'] = str(python_path)
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False
    
    return False


def run_command(cmd, description, check=True):
    """Run a command and handle output"""
    print(f"\n🔄 {description}")
    
    # Use virtual environment Python if available
    if cmd[0] == 'python3' and 'PYTHON_PATH' in os.environ:
        cmd[0] = os.environ['PYTHON_PATH']
    
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=check, capture_output=False, text=True)
        print(f"✅ {description} completed successfully")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Test microservices version sync locally')
    parser.add_argument('--github-token', 
                       help='GitHub token for AppState queries (can also use GITHUB_TOKEN env var)')
    parser.add_argument('--dry-run', 
                       action='store_true',
                       help='Run in dry-run mode (no actual updates)')
    parser.add_argument('--verbose', '-v', 
                       action='store_true',
                       help='Verbose output')
    parser.add_argument('--skip-appstate', 
                       action='store_true',
                       help='Skip AppState queries (for testing extraction only)')
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not Path('charts/frontegg-core-services/values.yaml').exists():
        print("Error: Please run this script from the helm-charts repository root")
        return 1
    
    # Check GitHub token
    token = args.github_token or os.environ.get('GITHUB_TOKEN')
    if not token and not args.skip_appstate:
        print("Warning: No GitHub token provided. Use --github-token or set GITHUB_TOKEN env var")
        print("Running with --skip-appstate to test extraction only")
        args.skip_appstate = True
    
    # Create output directory
    output_dir = Path('scripts/output')
    output_dir.mkdir(exist_ok=True)
    
    print("🚀 Starting local microservices version sync test")
    print(f"Output directory: {output_dir}")
    
    # Step 0: Setup virtual environment
    if not setup_virtual_environment():
        print("❌ Failed to setup virtual environment")
        return 1
    
    # Step 1: Extract services
    extract_cmd = [
        'python3', 'scripts/extract_services.py',
        '--output-dir', str(output_dir)
    ]
    if args.verbose:
        extract_cmd.append('--verbose')
    
    if not run_command(extract_cmd, "Extracting microservices from Helm values"):
        return 1
    
    if args.skip_appstate:
        print("\n✅ Extraction test completed successfully!")
        print(f"Check the output files in {output_dir}/")
        return 0
    
    # Step 2: Query AppState
    query_cmd = [
        'python3', 'scripts/query_appstate.py',
        '--services-file', str(output_dir / 'all_services.json'),
        '--output', str(output_dir / 'appstate_versions.json'),
        '--token', token
    ]
    if args.verbose:
        query_cmd.append('--verbose')
    
    if not run_command(query_cmd, "Querying AppState repository"):
        return 1
    
    # Step 3: Compare versions
    compare_cmd = [
        'python3', 'scripts/compare_versions.py',
        '--services-file', str(output_dir / 'all_services.json'),
        '--appstate-file', str(output_dir / 'appstate_versions.json'),
        '--output', str(output_dir / 'comparison_results.json'),
        '--summary-file', str(output_dir / 'summary.md')
    ]
    if args.verbose:
        compare_cmd.append('--verbose')
    
    if not run_command(compare_cmd, "Comparing versions"):
        return 1
    
    # Step 4: Update values (dry-run or actual)
    update_cmd = [
        'python3', 'scripts/update_values.py',
        '--comparison-file', str(output_dir / 'comparison_results.json')
    ]
    if args.dry_run:
        update_cmd.append('--dry-run')
    if args.verbose:
        update_cmd.append('--verbose')
    
    if not run_command(update_cmd, "Updating Helm values"):
        return 1
    
    print("\n🎉 All steps completed successfully!")
    print(f"\nOutput files created in {output_dir}/:")
    for file in output_dir.glob('*'):
        if file.is_file():
            print(f"  - {file.name}")
    
    print(f"\nTo view the summary:")
    print(f"  cat {output_dir}/summary.md")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
