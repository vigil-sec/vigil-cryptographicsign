# Vigil CLI - Developer Guide

A thin, untrusted CLI wrapper for the Vigil cryptographic proof service. Gate sensitive agent actions, request execution proofs, and monitor system state.

## Philosophy

**This CLI is infrastructure, not an application.**

- ❌ Never holds private keys
- ❌ Never performs signing
- ❌ Never mutates trusted state
- ✅ Makes HTTP calls to the service
- ✅ Returns structured responses
- ✅ Designed for automation and agents

The cryptographic trust lives entirely server-side in the Vigil service.

## Installation

### From source

```bash
cd vigil-cryptographicsign
pip install -e .
```

This registers the `vigil` command globally.

### Verify installation

```bash
vigil --version
vigil --help
```

## Configuration

The CLI reads from environment variables:

```bash
# Service endpoint (required)
export VIGIL_ENDPOINT=http://localhost:5000

# Optional: project identifier
export VIGIL_PROJECT_ID=my-project
```

Default endpoint: `http://localhost:5000`

## Commands

### vigil prove

Request a cryptographic proof before an agent performs an action.

```bash
vigil prove \
  --agent-id <id> \
  --action-hash <hash> \
  --policy-id <policy>
```

**Arguments:**
- `--agent-id` (required): Identifier of the agent
- `--action-hash` (required): SHA256 hash of the action (format: `sha256:...`)
- `--policy-id` (required): Policy governing this action

**Options:**
- `--json`: Output as machine-readable JSON
- `--quiet`: Exit code only, no stdout

**Exit codes:**
- `0`: Proof granted
- `1`: Proof denied or error

**Example:**

```bash
$ vigil prove \
    --agent-id agent-42 \
    --action-hash "sha256:abc123def456" \
    --policy-id "policy-prod-safe"

✓ Proof granted
  Receipt ID: receipt-000001
  Agent: agent-42
  Policy: policy-prod-safe
  Merkle Root: 79ae3195d57b7cef...
  Timestamp: 1705978903
```

**JSON output:**

```bash
$ vigil prove \
    --agent-id agent-42 \
    --action-hash "sha256:abc123def456" \
    --policy-id "policy-prod-safe" \
    --json

{
  "receipt_id": "receipt-000001",
  "agent_id": "agent-42",
  "action_hash": "sha256:abc123def456",
  "policy_id": "policy-prod-safe",
  "merkle_root": "79ae3195d57b7cef5e478a998f260040c4c716f8ae8a49be636e9c852c8af692",
  "timestamp": 1705978903,
  "signature": "cd0af9999efe8b33d8..."
}
```

**In scripts:**

```bash
# Capture result
RECEIPT=$(vigil prove --agent-id bot --action-hash "sha256:action" --policy-id safe --json)

# Check result
if vigil prove --agent-id bot --action-hash "sha256:action" --policy-id safe --quiet; then
  echo "Action approved"
else
  echo "Action denied"
  exit 1
fi
```

### vigil verify

Verify an execution receipt without trusting the Vigil server.

```bash
vigil verify <receipt-file>
```

**Arguments:**
- `receipt-file`: Path to receipt JSON file

**Options:**
- `--quiet`: Exit code only, no stdout

**Exit codes:**
- `0`: Signature is valid
- `1`: Signature is invalid or file not found

**Example:**

```bash
$ vigil verify receipt.json

✓ VALID signature
  Receipt ID: receipt-000001
```

**Invalid receipt:**

```bash
$ vigil verify bad-receipt.json

✗ INVALID signature
  Receipt ID: receipt-000001

$ echo $?
1
```

**In scripts:**

```bash
if vigil verify saved-receipt.json; then
  echo "Action is still approved"
else
  echo "Signature doesn't match"
  exit 1
fi
```

### vigil status

Read-only system monitoring. Shows current state of the proof service.

```bash
vigil status [--json] [--quiet]
```

**Options:**
- `--json`: Output as JSON
- `--quiet`: Suppress output

**Exit codes:**
- `0`: Success
- `1`: Connection error

**Example:**

```bash
$ vigil status

✓ System Status
  Merkle Root: 79ae3195d57b7cef5e478a998f260040...
  Entry Count: 42
  
  Recent Entries:
    [40] agent=deployer, policy=prod-safe
    [41] agent=scheduler, policy=data-backup
    [42] agent=monitor, policy=health-check
```

**JSON output:**

```bash
$ vigil status --json

{
  "merkle_root": "79ae3195d57b7cef5e478a998f260040c4c716f8ae8a49be636e9c852c8af692",
  "entry_count": 42,
  "entries": [
    {
      "sequence": 1,
      "timestamp": 1705978903,
      "agent_id": "agent-42",
      "action_hash": "sha256:abc123...",
      "policy_id": "policy-prod-safe",
      "merkle_root_after": "79ae3195d57b7cef..."
    }
  ]
}
```

**Health check:**

```bash
if vigil status --quiet; then
  echo "Service is healthy"
else
  echo "Service is down"
  exit 1
fi
```

### vigil guard

Gate command execution with proof requirement.

```bash
vigil guard \
  --agent-id <id> \
  --policy-id <policy> \
  -- <command...>
```

**Arguments:**
- `--agent-id` (required): Agent requesting execution
- `--policy-id` (required): Policy to enforce
- `<command...>`: Command to execute (everything after `--`)

**Options:**
- `--json`: Output proof as JSON

**Exit codes:**
- `0`: Proof granted AND command succeeded
- `1`: Proof denied OR command failed (command exit code if granted)

**Example - Safe deployment:**

```bash
vigil guard \
  --agent-id deployer \
  --policy-id prod-safe \
  -- terraform apply -auto-approve

✓ Proof granted for: terraform apply -auto-approve
Terraform will perform the following actions:
  # ...
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
```

**Example - Denied:**

```bash
vigil guard \
  --agent-id deployer \
  --policy-id dangerous \
  -- rm -rf /data

✗ Guard denied: Policy 'dangerous' not approved
```

**In shell scripts:**

```bash
#!/bin/bash
set -e

vigil guard \
  --agent-id backup-service \
  --policy-id data-backup \
  -- /usr/local/bin/backup-database.sh

vigil guard \
  --agent-id backup-service \
  --policy-id data-upload \
  -- aws s3 sync /backups s3://backups/
```

**In automation:**

```bash
# GitHub Actions
- name: Deploy with Vigil gate
  env:
    VIGIL_ENDPOINT: https://proof.example.com
  run: |
    vigil guard \
      --agent-id github-actions \
      --policy-id deploy-prod \
      -- ./scripts/deploy.sh production
```

## Use Cases

### 1. Agent Execution Gate

Require proof before letting an agent act:

```bash
# In agent code
agent_decision = llm.decide_action()
action_hash = hash(agent_decision)

result = subprocess.run([
  'vigil', 'prove',
  '--agent-id', os.environ['AGENT_ID'],
  '--action-hash', action_hash,
  '--policy-id', 'agent-safe'
])

if result.returncode == 0:
  execute_action(agent_decision)
else:
  log_denied(agent_decision)
```

### 2. Deployment Pipeline

Gate infrastructure changes:

```bash
#!/bin/bash
set -e

# Request proof for infrastructure change
PROOF=$(vigil prove \
  --agent-id ci-system \
  --action-hash "$(sha256sum Terraform.tf | cut -d' ' -f1)" \
  --policy-id prod-deploy \
  --json)

if [ $? -eq 0 ]; then
  # Save proof for audit
  echo "$PROOF" > proof-$(date +%s).json
  
  # Execute deployment
  terraform apply -auto-approve
else
  echo "Deployment blocked by policy"
  exit 1
fi
```

### 3. Batch Job Authorization

Require proof for each job:

```python
import subprocess
import sys
import json

class GuardedAgent:
    def __init__(self, agent_id, vigil_endpoint):
        self.agent_id = agent_id
        self.vigil_endpoint = vigil_endpoint
    
    def execute_with_proof(self, action_hash, policy_id, command):
        """Execute command only if proof is granted."""
        result = subprocess.run([
            'vigil', 'prove',
            '--agent-id', self.agent_id,
            '--action-hash', action_hash,
            '--policy-id', policy_id,
            '--quiet'
        ], env={'VIGIL_ENDPOINT': self.vigil_endpoint})
        
        if result.returncode == 0:
            return subprocess.run(command)
        else:
            sys.stderr.write(f"Proof denied for {action_hash}\n")
            return 1

# Usage
agent = GuardedAgent('batch-processor', 'http://proof-service:5000')
agent.execute_with_proof(
    'sha256:' + hashlib.sha256(b'process_batch_001').hexdigest(),
    'batch-safe',
    ['python', 'process_batch.py']
)
```

### 4. Audit Trail Monitoring

Monitor who did what:

```bash
#!/bin/bash

# Show recent actions
vigil status --json | jq '.entries[-10:] | .[] | {agent: .agent_id, policy: .policy_id, time: .timestamp}'

# Verify integrity
ROOT_BEFORE=$(vigil status --json | jq -r '.merkle_root')
sleep 10
ROOT_AFTER=$(vigil status --json | jq -r '.merkle_root')

if [ "$ROOT_BEFORE" != "$ROOT_AFTER" ]; then
  echo "System state changed"
else
  echo "System state stable"
fi
```

## Design Principles

### Security Boundaries

```
┌─────────────────────────────┐
│   UNTRUSTED (This CLI)      │
│                             │
│   • Parse arguments         │
│   • Make HTTP calls         │
│   • Display results         │
└─────────┬───────────────────┘
          │ HTTP
          ↓
┌─────────────────────────────┐
│   TRUSTED (Vigil Service)   │
│                             │
│   • Hold private keys       │
│   • Compute signatures      │
│   • Maintain audit log      │
│   • Enforce policies        │
└─────────────────────────────┘
```

### Exit Codes Matter

The CLI uses standard Unix exit codes for automation:

- `0`: Success - proof granted, action allowed, signature valid
- `1`: Failure - proof denied, action blocked, signature invalid

This makes it suitable for shell scripts, CI/CD pipelines, and agent logic.

### Machine-Readable Output

Use `--json` flag for parsing by machines:

```bash
# Human-readable (default)
$ vigil prove ... 
✓ Proof granted

# Machine-readable
$ vigil prove ... --json
{...JSON...}
```

### No Configuration Files

The CLI reads only from environment variables. No config files, no credentials files, no complexity.

```bash
export VIGIL_ENDPOINT=https://proof.example.com
vigil prove --agent-id bot --action-hash sha256:... --policy-id safe
```

## Troubleshooting

### Connection Error

```
✗ Proof failed: Connection refused
```

**Cause:** Service not running or wrong endpoint

**Solution:**
```bash
# Check service is running
curl http://localhost:5000/health

# Set correct endpoint
export VIGIL_ENDPOINT=http://correct-host:5000
vigil prove ...
```

### Invalid Argument

```
error: the following arguments are required: --agent-id
```

**Solution:**
```bash
vigil prove --help  # See required arguments
```

### Receipt File Not Found

```
✗ Receipt file not found: /path/to/receipt.json
```

**Solution:**
```bash
# Make sure file exists
ls -l /path/to/receipt.json

# Save output from prove command first
vigil prove ... --json > receipt.json
vigil verify receipt.json
```

## Architecture

The CLI is intentionally minimal:

- **client.py**: HTTP wrapper (makes calls, parses responses)
- **commands/**: Individual command implementations
- **vigil.py**: Main entry point (argument parsing, dispatch)

All cryptographic operations happen server-side.

## Reference

For detailed information about the Vigil service architecture, see [ARCHITECTURE.md](ARCHITECTURE.md) and [README.md](README.md).

---

**Status:** Production-ready prototype  
**Version:** 0.1.0  
**Trust Model:** Untrusted CLI, trusted server
