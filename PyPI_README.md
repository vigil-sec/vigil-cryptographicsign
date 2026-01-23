# Vigil CLI

CLI wrapper for the Vigil cryptographic proof service. Request and verify cryptographic proofs for agent actions.

```bash
$ vigil prove --agent-id mybot --action-hash sha256:abc123 --policy-id safe
{
  "agent_id": "mybot",
  "action_hash": "sha256:abc123",
  "signature": "...",
  "timestamp": "2026-01-23T..."
}

$ vigil verify receipt.json
✓ Valid signature
```

## Install

```bash
pip install vigil-cli
```

## Quick Start

Set the service endpoint:
```bash
export VIGIL_ENDPOINT=http://localhost:5000
```

Request a proof:
```bash
vigil prove \
  --agent-id agent-42 \
  --action-hash sha256:abcd1234 \
  --policy-id prod-safe
```

Gate a command:
```bash
vigil guard \
  --agent-id deployer \
  --policy-id prod-safe \
  -- terraform apply
```

## Commands

- **`vigil prove`** — Request cryptographic proof before action
- **`vigil verify`** — Verify an execution receipt signature
- **`vigil status`** — Read-only system monitoring
- **`vigil guard`** — Gate command execution with proof requirement

## Documentation

- **[Full CLI reference](https://github.com/rom-mvp/vigil-cryptographicsign/blob/main/CLI.md)** — All commands, flags, and examples
- **[Integration guide](https://github.com/rom-mvp/vigil-cryptographicsign/blob/main/AGENT_GUARD.md)** — Agent patterns, Kubernetes, CI/CD
- **[Architecture](https://github.com/rom-mvp/vigil-cryptographicsign/blob/main/ARCHITECTURE.md)** — System design and trust boundaries

## ⚠️ Security Disclaimer

**This CLI is UNTRUSTED.**

- CLI makes HTTP calls to the Vigil proof service
- CLI never holds private keys
- CLI never performs cryptographic signing
- All cryptographic operations happen server-side

The **Vigil proof service** is the AUTHORITY. It holds the private keys and creates all signatures.

For production: Deploy the Vigil proof service in a secure environment (hardware enclave, confidential container, or air-gapped server) and point this CLI to it.

```
┌─────────────────────────────┐
│   UNTRUSTED CLI (This)      │  ← You install this via PyPI
│   client.py                 │
│   commands/*.py             │
└──────────┬──────────────────┘
           │ HTTP Calls
           ↓
┌─────────────────────────────┐
│   TRUSTED SERVICE           │  ← Deploy separately (Docker, K8s, etc.)
│   Holds private keys        │
│   Creates signatures        │
│   main.py on port 5000      │
└─────────────────────────────┘
```

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `VIGIL_ENDPOINT` | `http://localhost:5000` | Service URL |
| `VIGIL_PROJECT_ID` | Not set | Optional project identifier |

## License

MIT
