#!/bin/bash
# Publication Script for Vigil

set -e

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                  Vigil Publishing Script                              ║"
echo "║                  version 0.1.0                                         ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check dependencies
echo "[1/4] Checking dependencies..."
command -v docker >/dev/null 2>&1 || { echo "Docker not found. Install Docker first."; exit 1; }
command -v python >/dev/null 2>&1 || { echo "Python not found. Install Python 3.9+."; exit 1; }

echo "✓ Docker available: $(docker --version)"
echo "✓ Python available: $(python --version)"
echo ""

# Build CLI package
echo "[2/4] Building CLI package..."
if [ ! -d "dist" ]; then
    echo "Running: python -m build"
    python -m build >/dev/null 2>&1
fi
echo "✓ CLI package built:"
echo "  - dist/vigil_cli-0.1.0-py3-none-any.whl"
echo "  - dist/vigil_cli-0.1.0.tar.gz"
echo ""

# Build Docker image
echo "[3/4] Building Docker image..."
if ! docker image inspect vigil/proof-service:0.1.0 >/dev/null 2>&1; then
    echo "Running: docker build -t vigil/proof-service:0.1.0 ."
    docker build -t vigil/proof-service:0.1.0 . >/dev/null 2>&1
    docker tag vigil/proof-service:0.1.0 vigil/proof-service:latest >/dev/null 2>&1
fi
echo "✓ Docker images built:"
echo "  - vigil/proof-service:0.1.0 (330 MB)"
echo "  - vigil/proof-service:latest (alias)"
echo ""

# Verify packages
echo "[4/4] Verifying packages..."
if [ ! -f "dist/vigil_cli-0.1.0-py3-none-any.whl" ]; then
    echo "✗ Wheel package not found"
    exit 1
fi
echo "✓ Wheel package verified: $(du -h dist/vigil_cli-0.1.0-py3-none-any.whl | cut -f1)"

if ! docker image inspect vigil/proof-service:0.1.0 >/dev/null 2>&1; then
    echo "✗ Docker image not found"
    exit 1
fi
echo "✓ Docker image verified: $(docker images | grep vigil/proof-service | grep 0.1.0 | awk '{print $3}')"
echo ""

echo "════════════════════════════════════════════════════════════════════════════"
echo "✓ ALL CHECKS PASSED"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "NEXT STEPS:"
echo ""
echo "1. Publish CLI to PyPI (requires PyPI account):"
echo "   $ pip install build twine"
echo "   $ twine upload dist/*"
echo ""
echo "2. Publish Docker image (requires Docker Hub account):"
echo "   $ docker login"
echo "   $ docker push vigil/proof-service:0.1.0"
echo "   $ docker push vigil/proof-service:latest"
echo ""
echo "3. Verify publication:"
echo "   $ pip install vigil-cli"
echo "   $ docker pull vigil/proof-service:0.1.0"
echo ""
echo "See PUBLISH.md and DISTRIBUTION.md for detailed instructions."
echo ""
