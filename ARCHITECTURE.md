# Vigil - Architecture & Migration Guide

This document explains the Vigil MVP architecture and how it will migrate unchanged into a hardware enclave.

## System Architecture

### Trust Boundary

```
┌─────────────────────────────────────────────────────┐
│                  UNTRUSTED HOST                      │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │     Flask REST API (host/api.py)             │  │
│  │  POST /prove - Accepts proof requests        │  │
│  │  POST /verify - Verifies receipts            │  │
│  │  GET /audit-log - Returns log entries        │  │
│  └──────────────────────────────────────────────┘  │
│           ↑                              ↑           │
│           │  RPC/vsock (in production)  │           │
│           ↓                              ↓           │
│  ┌──────────────────────────────────────────────┐  │
│  │  Cross-Trust-Boundary Interface              │  │
│  │  Signer.prove() - Single entry point         │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                        ↑
                        │
┌─────────────────────────────────────────────────────┐
│            TRUSTED CORE (future: TEE)               │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  key_manager.py                              │  │
│  │  - Holds Ed25519 private key (sealed)        │  │
│  │  - Never exported to host                    │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  audit_log.py                                │  │
│  │  - Append-only log                           │  │
│  │  - Merkle tree commitment                    │  │
│  │  - Tamper detection                          │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  signer.py                                   │  │
│  │  - prove() - Core signing logic              │  │
│  │  - Enforces: audit log FIRST, then sign     │  │
│  │  - Binds signature to Merkle root           │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  execution_receipt.py                        │  │
│  │  - Signed proof structure                    │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Data Flow: Proving an Action

```
1. Agent/Orchestrator calls:
   POST http://localhost:5000/prove
   {
     "agent_id": "agent-42",
     "action_hash": "sha256:...",
     "policy_id": "policy-default"
   }

2. Host API validates request and calls:
   receipt = signer.prove(agent_id, action_hash, policy_id)

3. Inside trusted_core (THIS MOVES INTO ENCLAVE):
   a) Append to audit log
      log_entry = audit_log.append(...)
      → Updates Merkle root
   
   b) Get Merkle root
      merkle_root = audit_log.get_root()
   
   c) Create receipt
      receipt = ExecutionReceipt(
        agent_id=agent_id,
        action_hash=action_hash,
        policy_id=policy_id,
        merkle_root=merkle_root,  ← CRITICAL: bound to log
        timestamp=now,
        signature=""
      )
   
   d) Sign the receipt
      signature = private_key.sign(
        f"{agent_id}|{action_hash}|{policy_id}|{merkle_root}|{timestamp}"
      )
      receipt.signature = signature.hex()

4. Host returns receipt to caller
   {
     "receipt_id": "receipt-000001",
     "agent_id": "agent-42",
     "action_hash": "sha256:...",
     "policy_id": "policy-default",
     "merkle_root": "0x5a7f...",
     "timestamp": 1705978903,
     "signature": "0x48f7d2e...",
   }

5. Caller can verify signature using public key
   (no access to private key needed)
```

## Security Properties

### 1. No Log = No Signature

Every signature includes the current Merkle root of the audit log:

```
signed_bytes = agent_id | action_hash | policy_id | merkle_root | timestamp
signature = SIGN(private_key, signed_bytes)
```

If the audit log is missing or tampered with, the signature becomes invalid.

### 2. Audit Log Tampering Detection

The Merkle tree commits to the entire history:

```
Merkle Tree:
              Root (0x5a7f...)
             /                \
        Hash(H0,H1)      Hash(H2,H3)
        /        \       /        \
      H(E0)    H(E1)   H(E2)    H(E3)
      |        |       |        |
     Entry0  Entry1  Entry2  Entry3
```

If any entry is modified, the root changes immediately:

```
entry0.agent_id = "hacker" → H(E0) changes
  → Hash(H0,H1) changes
    → Root changes
      → All signatures that include this root become invalid
```

### 3. Signature Binding to Context

Each receipt signature encodes the EXACT state of the system:

- **agent_id**: Who performed the action
- **action_hash**: What action was taken
- **policy_id**: Which policy governed it
- **merkle_root**: The ENTIRE audit history at that moment
- **timestamp**: When this happened

Changing ANY of these makes the signature invalid.

## Migration Path: Software → Hardware Enclave

### Phase 1: Software MVP (Current)

```
Process Memory
├── trusted_core/ (simulated enclave)
│   ├── KeyManager
│   ├── AuditLog
│   └── Signer
└── host/ (untrusted code)
    └── Flask API
```

**Security assumption**: OS-level isolation (in reality: weak)

### Phase 2: AWS Nitro Enclave

```
EC2 Instance (Untrusted Host)
├── Flask API (host/api.py)
└── vsock connection to Enclave (port 8000)

AWS Nitro Enclave (Trusted Core)
├── vsock listener (port 8000)
├── trusted_core/ (UNCHANGED)
│   ├── KeyManager (keys sealed by Nitro attestation)
│   ├── AuditLog
│   └── Signer
└── Audit log backed by enclave memory (encrypted at rest)
```

**Migration checklist**:
- ✅ No code changes in `trusted_core/`
- ✅ No code changes in signing logic
- ✅ No code changes in audit commitment
- ⚠️ Replace in-process `signer` calls with RPC over vsock
- ⚠️ Add TLS for vsock communication
- ⚠️ Verify Nitro attestation document before accepting requests

### Phase 3: Production Hardening

```
AWS Nitro Enclave
├── Attestation service (verify caller identity)
├── Key sealing (KMS integration)
├── Rate limiting (per-agent)
├── Audit log persistence (encrypted, immutable)
└── trusted_core/ (UNCHANGED)
```

## Key Takeaways

1. **Trust boundary is explicit**: Code marked `# THIS MOVES INTO ENCLAVE` runs in the trusted zone
2. **No runtime surprises**: All signing logic is deterministic and reproducible
3. **Audit log is the source of truth**: Everything goes through it
4. **Cryptographic commitment**: Merkle root + signature = tamper-proof proof
5. **Future-proof**: Today's software becomes tomorrow's enclave code without modification

## Code Organization

```
trusted_core/           # THIS MOVES INTO ENCLAVE
├── __init__.py
├── key_manager.py      # Sealing + key generation
├── audit_log.py        # Append-only log + Merkle tree
├── signer.py           # Core signing logic (no log = no signature)
└── execution_receipt.py # Signed proof structure

host/                   # UNTRUSTED HOST CODE
├── __init__.py
└── api.py              # REST interface to signing

main.py                 # Entry point (orchestrates both)
```

## Running the MVP

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py

# In another terminal:
curl -X POST http://localhost:5000/prove \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-42",
    "action_hash": "sha256:abc123...",
    "policy_id": "policy-default"
  }'

# Check audit log
curl http://localhost:5000/audit-log
```

## References

- [AWS Nitro Enclave Architecture](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/nitro-enclaves-architecture.html)
- [Ed25519 Signature Scheme](https://tools.ietf.org/html/rfc8032)
- [Merkle Trees for Integrity](https://en.wikipedia.org/wiki/Merkle_tree)
- [Zero-Knowledge Proofs (future work)](https://en.wikipedia.org/wiki/Zero-knowledge_proof)
