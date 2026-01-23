# Vigil Distribution

Two separate packages for secure activation and proof service.

## Package 1: vigil-cli (PyPI)

**The Activation Surface** — Untrusted CLI clients install this.

```bash
pip install vigil-cli
```

### What's Included
- CLI wrapper (`vigil` command)
- HTTP client to proof service
- Commands: prove, verify, status, guard
- No cryptographic operations
- No private keys

### Built Package
```
dist/vigil_cli-0.1.0-py3-none-any.whl    (9.3 KB)
dist/vigil_cli-0.1.0.tar.gz               (11 KB)
```

### Configuration
```bash
export VIGIL_ENDPOINT=http://localhost:5000
vigil prove --agent-id bot --action-hash sha256:abc --policy-id safe
```

### PyPI Entry
- **Name**: vigil-cli
- **Version**: 0.1.0
- **URL**: https://pypi.org/project/vigil-cli
- **README**: [PyPI_README.md](PyPI_README.md)

### Installation Target
- CI/CD systems
- Client machines
- Agent servers
- Anywhere that needs to request proofs

---

## Package 2: vigil/proof-service (Docker)

**The Authority Surface** — Proof service runs this with private keys.

```bash
docker run -d -p 5000:5000 vigil/proof-service:0.1.0
```

### What's Included
- Flask API server
- Ed25519 key manager (private keys)
- Merkle tree audit log
- Signing logic
- Health checks

### Built Image
```
vigil/proof-service:0.1.0
vigil/proof-service:latest
```

### Deployment
```bash
# Local testing
docker run -p 5000:5000 vigil/proof-service:0.1.0

# Production (Kubernetes)
kubectl apply -f vigil-deployment.yaml

# Production (with environment)
docker run -d \
  -p 5000:5000 \
  -v /secure/keys:/app/keys \
  -e LOG_LEVEL=INFO \
  vigil/proof-service:0.1.0
```

### Security
- Runs with minimal privileges
- Private keys in sealed files (mode 0o600)
- Health checks enabled
- No external network access needed
- Slim base image

### Registry
- **Name**: vigil/proof-service
- **Version**: 0.1.0
- **Registries**: Docker Hub (or your private registry)

### Deployment Target
- Kubernetes clusters
- Docker-enabled servers
- Confidential computing environments
- Air-gapped networks (local Docker)

---

## Distribution Flow

```
DEVELOPER/STARTUP
├── Install CLI
│   $ pip install vigil-cli
│   ✓ 9.3 KB wheel from PyPI
│   ✓ No configuration needed
│   ✓ Set VIGIL_ENDPOINT env var
│
└── Connect to Service
    $ vigil prove ...
    ↓ (HTTP request)
    PROOF SERVICE
    ├── Runs as Docker container
    │   docker run vigil/proof-service:0.1.0
    │   ✓ 330 MB image
    │   ✓ Holds private keys
    │   ✓ Creates signatures
    │
    └── Returns signed receipt
        ↓ (JSON response)
        CLI receives proof
```

---

## Step-by-Step Publishing

### 1. Publish CLI to PyPI

**Prerequisites**
```bash
pip install build twine
```

**Build**
```bash
cd vigil-cryptographicsign
python -m build
```

**Test (Optional)**
```bash
twine upload --repository testpypi dist/*
# Install from test: pip install -i https://test.pypi.org/simple/ vigil-cli
```

**Publish**
```bash
twine upload dist/*
# Requires PyPI account and credentials
```

**Verify**
```bash
pip install vigil-cli
vigil --help
```

### 2. Publish Service to Docker Hub

**Prerequisites**
```bash
docker login
```

**Build**
```bash
docker build -t vigil/proof-service:0.1.0 .
docker tag vigil/proof-service:0.1.0 vigil/proof-service:latest
```

**Test**
```bash
docker run -p 5000:5000 vigil/proof-service:0.1.0
# In another terminal:
curl http://localhost:5000/health
```

**Push**
```bash
docker push vigil/proof-service:0.1.0
docker push vigil/proof-service:latest
```

**Verify**
```bash
docker pull vigil/proof-service:latest
```

---

## Version Management

Update both versions together:

**setup.py**
```python
version="0.1.0"
```

**pyproject.toml**
```toml
version = "0.1.0"
```

**Dockerfile** (implicit via build)
```
# Tag during build:
docker build -t vigil/proof-service:0.1.0 .
```

---

## Security Checklist

### CLI Package (PyPI)

- [x] No private keys bundled
- [x] HTTP-only communication (upgrade to HTTPS)
- [x] Minimal dependencies (requests only)
- [x] Exit codes properly implemented
- [x] Environment variable configuration
- [x] Clear disclaimer in README

### Service Image (Docker)

- [x] Slim base image (Python 3.11-slim)
- [x] Health check enabled
- [x] Private key file has secure permissions (0o600)
- [x] Logs configured (no key leakage)
- [x] Flask production-ready
- [x] Minimal attack surface

---

## End-User Experience

### Install & Use (5 minutes)

```bash
# 1. Install CLI
pip install vigil-cli

# 2. Run service locally (for testing)
docker run -d -p 5000:5000 vigil/proof-service:0.1.0

# 3. Use immediately
export VIGIL_ENDPOINT=http://localhost:5000
vigil prove --agent-id mybot --action-hash sha256:test --policy-id safe
```

### Production Deployment

```bash
# 1. Deploy service (once, in secure location)
kubectl apply -f vigil-deployment.yaml

# 2. Install CLI on all agents
pip install vigil-cli

# 3. Configure endpoint
export VIGIL_ENDPOINT=https://proof.company.com

# 4. Gate actions
vigil guard --agent-id deployer --policy-id prod-safe -- ./deploy.sh
```

---

## Files Changed/Created

### Created
- [PyPI_README.md](PyPI_README.md) — CLI package description for PyPI
- [Dockerfile](Dockerfile) — Service container definition
- [PUBLISH.md](PUBLISH.md) — Publishing instructions
- `dist/vigil_cli-0.1.0-py3-none-any.whl` — Built wheel
- `dist/vigil_cli-0.1.0.tar.gz` — Built source distribution

### Modified
- [setup.py](setup.py) — Added long_description, URLs, classifiers
- [pyproject.toml](pyproject.toml) — Updated for PyPI, added project URLs

### Unchanged (but packaged)
- `cli/` — CLI source code
- `trusted_core/` — Signing logic
- `host/` — Flask API
- `main.py` — Service entry point

---

## Next Steps

1. ✅ **Prepare packages** (done)
   - CLI built: `vigil_cli-0.1.0.whl`
   - Service built: `vigil/proof-service:0.1.0`

2. **Publish CLI**
   ```bash
   twine upload dist/*
   ```

3. **Publish Service**
   ```bash
   docker push vigil/proof-service:0.1.0
   ```

4. **Announce**
   - PyPI project page
   - Docker Hub page
   - GitHub releases
   - Documentation

5. **Monitor**
   - PyPI download stats
   - Docker Hub pull stats
   - GitHub issues

---

## Download & Install URLs

### PyPI (Once Published)
```
https://pypi.org/project/vigil-cli
pip install vigil-cli
```

### Docker (Once Pushed)
```
docker pull vigil/proof-service:0.1.0
docker run -p 5000:5000 vigil/proof-service:0.1.0
```

### GitHub Releases (Optional)
```
https://github.com/rom-mvp/vigil-cryptographicsign/releases
```

---

## Architecture Summary

```
┌────────────────────────────────────────────┐
│           UNTRUSTED LAYER                  │
│  vigil-cli (pip install vigil-cli)         │
│  ├── CLI commands (prove, verify, guard)   │
│  ├── HTTP client                           │
│  └── No private keys                       │
└────────────────────────────────────────────┘
           │
           │ HTTP/HTTPS
           ↓
┌────────────────────────────────────────────┐
│           TRUSTED LAYER                    │
│  vigil/proof-service (Docker container)    │
│  ├── Ed25519 key manager                   │
│  ├── Merkle tree audit log                 │
│  ├── Flask REST API                        │
│  └── Signature creation                    │
└────────────────────────────────────────────┘
```

This distribution model keeps the untrusted surface (CLI) separate from the trusted authority (service).
