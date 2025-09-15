#!/bin/bash
# Example usage of the microservices version sync scripts

set -e

echo "🚀 Microservices Version Sync - Example Usage"
echo "=============================================="

# Check if we're in the right directory
if [[ ! -f "charts/frontegg-core-services/values.yaml" ]]; then
    echo "❌ Error: Please run this script from the helm-charts repository root"
    exit 1
fi

# Create output directory
mkdir -p scripts/output
cd scripts/output

echo ""
echo "📦 Step 1: Installing dependencies..."

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "Creating and activating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment activated"
fi

pip install -r ../requirements.txt

echo ""
echo "🔍 Step 2: Extracting services from Helm values..."
python3 ../extract_services.py --verbose

echo ""
echo "📊 Services extracted:"
echo "- Core services: $(jq length core_services.json)"
echo "- Dashboard services: $(jq length dashboard_services.json)"
echo "- Total services: $(jq length all_services.json)"

echo ""
echo "📋 Service list:"
jq -r '.[] | "  - \(.service_name) (\(.chart)): \(.app_version)"' all_services.json

if [[ -n "$GITHUB_TOKEN" ]]; then
    echo ""
    echo "🔍 Step 3: Querying AppState repository..."
    python3 ../query_appstate.py --verbose
    
    echo ""
    echo "📊 Step 4: Comparing versions..."
    python3 ../compare_versions.py --verbose --summary-file summary.md
    
    echo ""
    echo "📄 Summary:"
    cat summary.md
    
    echo ""
    echo "🔧 Step 5: Checking what would be updated (dry-run)..."
    python3 ../update_values.py --dry-run --verbose
    
    echo ""
    echo "✅ All steps completed successfully!"
    echo ""
    echo "To apply the updates, run:"
    echo "  python3 scripts/update_values.py --verbose"
    
else
    echo ""
    echo "⚠️  GITHUB_TOKEN not set - skipping AppState queries"
    echo ""
    echo "To run the full sync:"
    echo "  export GITHUB_TOKEN='your_token_here'"
    echo "  ./scripts/example_usage.sh"
fi

echo ""
echo "📁 Output files created:"
ls -la *.json *.md 2>/dev/null || echo "  (no files created)"
