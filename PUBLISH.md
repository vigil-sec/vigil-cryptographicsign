# Publishing Vigil

Two-tier distribution: CLI on PyPI, Service in Docker.

## Part 1: Publish CLI to PyPI

**vigil-cli** is the untrusted activation surface. Install on client machines, CI/CD, agents.

### Prerequisites

```bash
pip install build twine
```

### Build

```bash
cd /path/to/vigil-cryptographicsign
python -m build
```

This creates:
- `dist/vigil_cli-0.1.0-py3-none-any.whl`
- `dist/vigil-cli-0.1.0.tar.gz`

### Publish to PyPI

```bash
# Test (staging)
twine upload --repository testpypi dist/*

# Production
twine upload dist/*
```

Then users install:
```bash
pip install vigil-cli
vigil --help
```

### Update Version

Edit `setup.py` and `pyproject.toml`:
```
version = "0.2.0"  # Change this
```

---

## Part 2: Publish Service to Docker

**vigil/proof-service** is the trusted authority surface. Runs with private keys.

### Prerequisites

- Docker installed
- Docker Hub account (or use your registry)

### Build Image

```bash
cd /path/to/vigil-cryptographicsign

# Build
docker build -t vigil/proof-service:0.1.0 .
docker tag vigil/proof-service:0.1.0 vigil/proof-service:latest

# Test locally
docker run -p 5000:5000 vigil/proof-service:0.1.0
# In another terminal:
curl http://localhost:5000/health
```

### Push to Docker Hub

```bash
# Login
docker login

# Push
docker push vigil/proof-service:0.1.0
docker push vigil/proof-service:latest
```

### Users Deploy

```bash
# Run service
docker run -d \
  --name vigil \
  -p 5000:5000 \
  -e LOG_LEVEL=INFO \
  vigil/proof-service:0.1.0

# Install CLI
pip install vigil-cli

# Use
export VIGIL_ENDPOINT=http://localhost:5000
vigil prove --agent-id test --action-hash sha256:abc --policy-id safe
```

---

## Deployment Architecture

```
┌──────────────────────────────────┐
│  Client Machine / CI/CD Agent    │
│  ┌────────────────────────────┐  │
│  │  vigil-cli (from PyPI)     │  │◄─ pip install vigil-cli
│  │  HTTP client wrapper       │  │
│  │  No private keys           │  │
│  └────────────────────────────┘  │
│              │                    │
│              │ HTTP              │
│              ↓                    │
│  ┌────────────────────────────┐  │
│  │  VIGIL_ENDPOINT            │  │
│  │  (remote or local)         │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│  Server / Kubernetes Cluster     │
│  ┌────────────────────────────┐  │
│  │  Docker: vigil:0.1.0       │◄─ docker run ...
│  │  main.py                   │
│  │  trusted_core (signing)    │
│  │  Holds private keys        │
│  │  Port 5000                 │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
```

---

## Environment Variables

### CLI
```bash
VIGIL_ENDPOINT=http://localhost:5000
VIGIL_PROJECT_ID=my-project
```

### Service
```bash
LOG_LEVEL=INFO
FLASK_ENV=production
```

---

## Version Management

Keep CLI and service versions in sync:

- `vigil-cli@0.1.0` → `vigil/proof-service:0.1.0`
- `vigil-cli@0.2.0` → `vigil/proof-service:0.2.0`

Both files need updates:
- CLI: `setup.py` and `pyproject.toml`
- Service: `Dockerfile` base image tags and `main.py`

---

## Security Checklist

- [ ] CLI is stateless (no config files, no secrets)
- [ ] Service runs in isolated container/enclave
- [ ] Private key file has mode 0o600 (read-only to service)
- [ ] Service endpoint is HTTPS in production
- [ ] Service runs with minimal privileges
- [ ] Docker image uses slim base (minimal attack surface)
- [ ] Health checks enabled
- [ ] Logs don't leak private keys or signatures

---

## Rollback

If issues found:

```bash
# CLI
pip install vigil-cli==0.0.9

# Service
docker run vigil/proof-service:0.0.9
```

---

## Next Steps

1. **First Release**
   ```bash
   twine upload dist/*  # vigil-cli to PyPI
   docker push vigil/proof-service:0.1.0
   ```

2. **Documentation**
   - Create PyPI page docs
   - Update README with installation instructions
   - Add deployment guide for Docker

3. **CI/CD Pipeline**
   - Automate builds on `git tag`
   - Run tests before publishing
   - Sign releases

