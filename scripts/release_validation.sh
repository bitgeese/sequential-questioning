#!/bin/bash
set -e

# Sequential Questioning MCP Server Release Validation Script
# This script validates the project's readiness for release

echo "=== Sequential Questioning MCP Server Release Validation ==="
echo "Validating version 1.0.0 readiness..."
echo

# Check environment
echo "Checking environment..."
if ! command -v python &> /dev/null; then
    echo "ERROR: Python not found. Please install Python 3.10+"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "WARNING: Docker not found. Container validation will be skipped."
    SKIP_DOCKER=true
fi

if ! command -v kubectl &> /dev/null; then
    echo "WARNING: kubectl not found. Kubernetes validation will be skipped."
    SKIP_K8S=true
fi

# Check Python version
PYTHON_VERSION=$(python --version | grep -Eo '[0-9]+\.[0-9]+')
if (( $(echo "$PYTHON_VERSION < 3.10" | bc -l) )); then
    echo "ERROR: Python 3.10+ is required, found $PYTHON_VERSION"
    exit 1
fi

echo "✅ Environment checks passed"
echo

# Check code quality
echo "Checking code quality..."
echo "Running linters..."

if ! command -v ruff &> /dev/null; then
    echo "Installing ruff..."
    pip install ruff
fi

if ! command -v black &> /dev/null; then
    echo "Installing black..."
    pip install black
fi

if ! command -v mypy &> /dev/null; then
    echo "Installing mypy..."
    pip install mypy
fi

# Run linters
ruff check app tests || { echo "❌ Ruff check failed"; exit 1; }
black --check app tests || { echo "❌ Black check failed"; exit 1; }
mypy app || { echo "❌ Type checking failed"; exit 1; }

echo "✅ Code quality checks passed"
echo

# Check tests
echo "Running tests..."
if ! command -v pytest &> /dev/null; then
    echo "Installing pytest and coverage..."
    pip install pytest pytest-cov
fi

# Run tests with coverage
pytest --cov=app tests/ || { echo "❌ Tests failed"; exit 1; }

# Check coverage threshold
COVERAGE=$(pytest --cov=app tests/ --cov-report=term-missing | grep TOTAL | awk '{print $4}' | sed 's/%//')
if (( $(echo "$COVERAGE < 90" | bc -l) )); then
    echo "❌ Test coverage is below 90% (current: $COVERAGE%)"
    exit 1
fi

echo "✅ Test coverage is $COVERAGE% (threshold: 90%)"
echo

# Check documentation
echo "Checking documentation..."
REQUIRED_DOCS=(
    "docs/architecture.md"
    "docs/api_reference.md"
    "docs/deployment.md"
    "docs/usage_examples.md"
    "docs/operational_runbook.md"
    "docs/final_deployment_plan.md"
    "docs/project_release_notes.md"
    "docs/production_deployment_guide.md"
    "CONTRIBUTING.md"
    "README.md"
)

for doc in "${REQUIRED_DOCS[@]}"; do
    if [ ! -f "$doc" ]; then
        echo "❌ Missing required documentation: $doc"
        exit 1
    fi
    
    # Check if doc is not empty
    if [ ! -s "$doc" ]; then
        echo "❌ Documentation file is empty: $doc"
        exit 1
    fi
done

echo "✅ Documentation checks passed"
echo

# Check Docker image build
if [ -z "$SKIP_DOCKER" ]; then
    echo "Building Docker image..."
    docker build -t sequential-questioning-test:1.0.0 . || { echo "❌ Docker build failed"; exit 1; }
    echo "✅ Docker image build successful"
    echo
fi

# Check Kubernetes configurations
if [ -z "$SKIP_K8S" ]; then
    echo "Validating Kubernetes configurations..."
    
    # Check base configurations
    for config in k8s/base/*.yaml; do
        kubectl apply --dry-run=client -f $config > /dev/null || { echo "❌ Invalid Kubernetes config: $config"; exit 1; }
    done
    
    # Check overlays with kustomize
    if command -v kustomize &> /dev/null; then
        for env in dev staging prod; do
            kustomize build k8s/overlays/$env | kubectl apply --dry-run=client -f - > /dev/null || { echo "❌ Invalid kustomize overlay: $env"; exit 1; }
        done
        echo "✅ Kubernetes configurations validated successfully"
    else
        echo "WARNING: kustomize not found, skipping overlay validation"
    fi
    echo
fi

# Check release artifacts
echo "Checking release artifacts..."
VERSION_FILE="app/version.py"

if [ ! -f "$VERSION_FILE" ]; then
    echo "❌ Missing version file: $VERSION_FILE"
    exit 1
fi

VERSION=$(grep -E "^__version__" "$VERSION_FILE" | cut -d '"' -f 2)
if [ "$VERSION" != "1.0.0" ]; then
    echo "❌ Version mismatch: Expected 1.0.0, found $VERSION in $VERSION_FILE"
    exit 1
fi

echo "✅ Release artifacts checked successfully"
echo

# Summary
echo "=== Release Validation Summary ==="
echo "✅ Environment: Passed"
echo "✅ Code Quality: Passed"
echo "✅ Tests: Passed ($COVERAGE% coverage)"
echo "✅ Documentation: Passed"
if [ -z "$SKIP_DOCKER" ]; then
    echo "✅ Docker Build: Passed"
else
    echo "⚠️ Docker Build: Skipped"
fi
if [ -z "$SKIP_K8S" ]; then
    echo "✅ Kubernetes Configs: Passed"
else
    echo "⚠️ Kubernetes Configs: Skipped"
fi
echo "✅ Release Artifacts: Passed"
echo
echo "🎉 All validation checks passed! The project is ready for release."
echo "Run the following command to create the release:"
echo "  git tag -a v1.0.0 -m \"Release v1.0.0\""
echo "  git push origin v1.0.0" 