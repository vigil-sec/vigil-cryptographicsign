# Vigil: Cryptographic Proof System for AI Agents

A software-only MVP prototype of a hardware-backed trust system for AI agents. This implementation demonstrates the architecture that will later run unchanged inside a TEE (AWS Nitro Enclave).

**Quick Start for Developers:**
```bash
pip install -e .                                    # Install CLI
python main.py                                      # Start service
vigil prove --agent-id bot --action-hash sha256:abc --policy-id safe
```

See [CLI.md](CLI.md) for full command reference.

## Overview

**Vigil** acts as a cryptographic notary for AI agent actions, producing tamper-evident, signed execution receipts. The core principle: **no log = no signature**.

The system enforces a strict trust boundary:
- **`trusted_core/`**: Future enclave (keys, signing, audit)
- **`host/`**: Untrusted environment (API, orchestration)
- **`cli/`**: Untrusted command wrapper (thin HTTP client)

## How It Works

1. **Host** receives a request to prove an agent action
2. **Host** forwards `(agent_id, action_hash, policy_id)` to **trusted_core** via well-defined RPC
3. **trusted_core** appends to audit log, computes Merkle root
4. **trusted_core** signs: `{agent_id, action_hash, policy_id, merkle_root, timestamp}` with Ed25519 private key
5. **Host** returns the signed `ExecutionReceipt` to the caller

## Architecture

### trusted_core/ (THIS MOVES INTO ENCLAVE)

**Key Modules:**

- **`key_manager.py`**: Simulates enclave key sealing. Generates and holds Ed25519 signing key.
- **`audit_log.py`**: Append-only log. Computes Merkle root over all entries.
- **`signer.py`**: Core signing logic. Refuses to sign unless audit log was updated first.
- **`execution_receipt.py`**: Structured proof output.

**Interface:**
```python
TrustedCore.prove(agent_id: str, action_hash: str, policy_id: str) -> ExecutionReceipt
```

### host/ (UNTRUSTED HOST CODE)

**Key Modules:**

- **`api.py`**: Minimal REST API (Flask).
  - `POST /prove`: Accept request, forward to trusted_core, return receipt
- **`client.py`**: Communication bridge to trusted_core.

## Security Properties

1. **Audit Log Tampering Detection**: Merkle tree root changes if any entry is modified
2. **Private Key Protection**: Never exposed to host
3. **Timestamped Proofs**: Each receipt includes Unix timestamp
4. **Immutable Execution History**: Append-only log enables forensic verification

## Quick Start

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run the MVP
```bash
python main.py
```

This starts:
- **Trusted Core**: Initializes keys and audit log (port 9999, internal only)
- **Host API**: Listens on `http://localhost:5000`

### Prove an Action

```bash
curl -X POST http://localhost:5000/prove \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-42",
    "action_hash": "sha256:abc123...",
    "policy_id": "policy-default"
  }'
```

**Response:**
```json
{
  "agent_id": "agent-42",
  "action_hash": "sha256:abc123...",
  "policy_id": "policy-default",
  "merkle_root": "0x5a7f...",
  "timestamp": 1705978903,
  "signature": "0x48f7d2e...",
  "receipt_id": "receipt-001"
}
```

## Roadmap: From Software to Hardware

This design is **intentionally enclave-ready**:

### Phase 1 (Current): Software MVP
✅ Runs on localhost  
✅ Demonstrates trust boundary patterns  
✅ Proves audit + signing logic

### Phase 2: AWS Nitro Enclave Migration
- Move `trusted_core/` into Nitro Enclave container
- Host calls enclave via attestation API
- Private keys sealed by AWS KMS
- Audit log stored in enclave-protected memory

### Phase 3: Production Hardening
- Attestation verification for remote callers
- Key rotation policies
- Decryption of sealed logs for authorized auditors
- Per-agent rate limiting

## Code Markers

Look for:
- `# THIS MOVES INTO ENCLAVE` - Code that migrates to TEE unchanged
- `# UNTRUSTED HOST CODE` - Host-side orchestration

## Minimal Dependencies

- `cryptography`: Ed25519 signing
- `flask`: REST API
- Python 3.9+

No external services, no dashboards, no auth systems. Pure trust boundary demonstration.

## Security Considerations

This is a **founder-grade prototype**. For production:
- Use hardware TPM instead of software key storage
- Implement rate limiting and DoS protection
- Add remote attestation for verifying enclave identity
- Persist audit logs to tamper-evident storage

## References

- [AWS Nitro Enclave Docs](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/nitro-enclaves.html)
- [Ed25519 RFC 8032](https://tools.ietf.org/html/rfc8032)
- [Merkle Tree Proofs](https://en.wikipedia.org/wiki/Merkle_tree)