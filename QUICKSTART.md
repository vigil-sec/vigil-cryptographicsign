# Vigil MVP - Quick Reference

## What This Is

A **founder-grade prototype** of a hardware-backed trust system for AI agents. The architecture is intentionally designed to migrate unchanged into a TEE (AWS Nitro Enclave).

**Core concept**: Acts as a cryptographic notary for AI agent actions. Every signature includes a commitment to the audit log, making the invariant **"no log = no signature"** cryptographically enforced.

## File Structure

```
vigil-cryptographicsign/
├── README.md                    # Project overview
├── ARCHITECTURE.md              # Trust boundaries & migration path
├── main.py                      # Entry point (orchestrates everything)
├── requirements.txt             # Dependencies (minimal)
├── test_vigil.py               # Integration test suite (all tests pass ✓)
├── verify_receipt.py           # Example offline verification
│
├── trusted_core/               # THIS MOVES INTO ENCLAVE
│   ├── __init__.py
│   ├── key_manager.py          # Ed25519 key generation & sealing
│   ├── audit_log.py            # Append-only log + Merkle root
│   ├── signer.py               # Core: prove() + verify()
│   └── execution_receipt.py    # Signed proof data structure
│
└── host/                       # UNTRUSTED HOST CODE
    ├── __init__.py
    └── api.py                  # Flask REST API (3 endpoints)
```

## Running

```bash
# Install
pip install -r requirements.txt

# Start server (listens on :5000)
python main.py

# Run tests
python test_vigil.py
```

## API (3 endpoints)

### 1. POST /prove
Request proof of an agent action.

```bash
curl -X POST http://localhost:5000/prove \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-42",
    "action_hash": "sha256:abc123...",
    "policy_id": "policy-default"
  }'
```

**Response**: ExecutionReceipt (signed by private key)
```json
{
  "receipt_id": "receipt-000001",
  "agent_id": "agent-42",
  "action_hash": "sha256:abc123...",
  "policy_id": "policy-default",
  "merkle_root": "0x5a7f...",
  "timestamp": 1705978903,
  "signature": "0x48f7d2e..."
}
```

### 2. POST /verify
Verify a receipt signature (no private key needed).

```bash
curl -X POST http://localhost:5000/verify \
  -H "Content-Type: application/json" \
  -d '{ receipt JSON }'
```

**Response**:
```json
{
  "receipt_id": "receipt-000001",
  "valid": true
}
```

### 3. GET /audit-log
View all audit log entries and Merkle root.

```bash
curl http://localhost:5000/audit-log
```

**Response**:
```json
{
  "merkle_root": "0x5a7f...",
  "entry_count": 4,
  "entries": [
    {
      "sequence": 1,
      "timestamp": 1705978903,
      "agent_id": "agent-42",
      "action_hash": "sha256:abc123...",
      "policy_id": "policy-default",
      "merkle_root_after": "0x5a7f..."
    }
  ]
}
```

## Key Security Properties

| Property | How It Works |
|----------|--------------|
| **No Log = No Signature** | Every signature includes merkle_root of audit log. Change the log → root changes → signature invalid |
| **Tamper Detection** | Merkle tree commits to entire history. Modify any entry → root changes → signature fails |
| **Immutable History** | Audit log is append-only. Entries can't be deleted or modified |
| **Key Protection** | Private key never exported. Only signed proofs leave the enclave |
| **Reproducible Proofs** | Same input → same signature (deterministic Ed25519) |

## Code Markers

Look for these comments in the code:

- **`# THIS MOVES INTO ENCLAVE`** → Code that migrates to TEE unchanged
  - `trusted_core/` directory (all files)
  
- **`# UNTRUSTED HOST CODE`** → Host-side orchestration
  - `host/` directory
  - `main.py` orchestration

## Architecture Highlights

### Signing Flow (Core Logic)
```
1. Append to audit log      ← CRITICAL: ALWAYS FIRST
2. Get Merkle root
3. Create receipt with merkle_root
4. Sign receipt with Ed25519
5. Return signed receipt
```

### Why This Works
The signature **binds** the proof to the audit log state:

```
signature = SIGN(private_key, 
  f"{agent_id}|{action_hash}|{policy_id}|{merkle_root}|{timestamp}")
```

If audit log changes → merkle_root changes → signature invalid

## Migration to Hardware Enclave

### Phase 1 (Today)
- Software-only MVP
- In-process signer
- Demonstrates trust boundary

### Phase 2 (AWS Nitro)
```
EC2 Host: Flask API (unchanged)
    ↓ vsock RPC
Enclave: trusted_core/ (UNCHANGED CODE)
    ↓ KMS sealing
AWS KMS: Private key protected
```

**Code changes needed**: Only RPC bridge (Flask ↔ vsock)  
**Core logic changes**: ZERO

## Dependencies

Minimal:
- `cryptography` - Ed25519 signing
- `flask` - REST API
- Python 3.9+

## Testing

```bash
# Full integration test (all features)
python test_vigil.py

# Offline verification demo
python verify_receipt.py

# Syntax check
python -m py_compile trusted_core/*.py host/*.py main.py
```

## Example: Offline Verification

Anyone with the public key can verify a receipt:

```python
from cryptography.hazmat.primitives import serialization

# Load public key (no private key needed!)
public_key = serialization.load_pem_public_key(pem_bytes)

# Reconstruct payload (exact order matters)
payload = f"{agent_id}|{action_hash}|{policy_id}|{merkle_root}|{timestamp}".encode()

# Verify
public_key.verify(signature_bytes, payload)  # Raises if invalid
```

## Design Philosophy

**NOT included** (intentionally minimal):
- ❌ Dashboards or UI
- ❌ Authentication systems
- ❌ Rate limiting
- ❌ Database persistence
- ❌ Complex config

**INCLUDED** (trust boundary essentials):
- ✅ Cryptographic signing (Ed25519)
- ✅ Audit log commitment (Merkle tree)
- ✅ "No log = no signature" enforcement
- ✅ Tamper detection
- ✅ Clear trust boundaries
- ✅ Production-quality crypto

## Next Steps

### For Production
1. Add Nitro Enclave wrapper
2. Implement vsock RPC
3. Add TLS for communication
4. Use AWS KMS for key sealing
5. Implement attestation verification
6. Add rate limiting & DoS protection

### For Research/Learning
1. Add zero-knowledge proofs
2. Implement multi-signer scenarios
3. Add key rotation policies
4. Explore recursive Merkle commitments

## References

- [AWS Nitro Enclave Docs](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/nitro-enclaves.html)
- [Ed25519 RFC 8032](https://tools.ietf.org/html/rfc8032)
- [Merkle Trees](https://en.wikipedia.org/wiki/Merkle_tree)

---

**Version**: MVP v0.1  
**Date**: January 2026  
**Status**: Founder-grade prototype ✓
