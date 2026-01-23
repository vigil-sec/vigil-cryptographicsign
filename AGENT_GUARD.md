# Using Vigil as an Agent Guard

This guide shows how to integrate Vigil into agent workflows to enforce cryptographic proof requirements before sensitive actions.

## Use Case 1: LLM Agent with Action Gating

An LLM agent that must request proof before executing actions:

```python
import hashlib
import json
import subprocess
from agent_core import Agent, decide_next_action

class GuardedAgent(Agent):
    def __init__(self, agent_id, policy_id, vigil_endpoint='http://localhost:5000'):
        super().__init__()
        self.agent_id = agent_id
        self.policy_id = policy_id
        self.vigil_endpoint = vigil_endpoint
    
    def execute_action(self, action):
        """Execute action only if cryptographic proof is granted."""
        
        # Serialize the action
        action_json = json.dumps(action, sort_keys=True)
        action_hash = hashlib.sha256(action_json.encode()).hexdigest()
        action_hash = f"sha256:{action_hash}"
        
        # Request proof from Vigil
        result = subprocess.run([
            'vigil', 'prove',
            '--agent-id', self.agent_id,
            '--action-hash', action_hash,
            '--policy-id', self.policy_id,
            '--quiet'
        ], env={'VIGIL_ENDPOINT': self.vigil_endpoint})
        
        if result.returncode == 0:
            # Proof granted - execute action
            print(f"✓ Action approved: {action['type']}")
            self.perform_action(action)
        else:
            # Proof denied - log and continue
            print(f"✗ Action blocked: {action['type']}")
            self.log_denial(action)

# Usage
agent = GuardedAgent(
    agent_id='research-bot',
    policy_id='safe-research',
    vigil_endpoint='http://vigil-service:5000'
)

# Agent operates normally, but sensitive actions require proof
while True:
    decision = agent.think()
    agent.execute_action(decision)
```

## Use Case 2: Terraform Deployment Pipeline

Gate infrastructure changes with Vigil:

```bash
#!/bin/bash
set -e

TERRAFORM_PLAN=$(terraform plan -json)
PLAN_HASH=$(echo "$TERRAFORM_PLAN" | sha256sum | cut -d' ' -f1)

echo "Requesting proof for infrastructure change..."

vigil prove \
  --agent-id ci-deployer \
  --action-hash "sha256:$PLAN_HASH" \
  --policy-id terraform-prod \
  --json > proof.json

if [ $? -eq 0 ]; then
  echo "✓ Infrastructure change approved"
  
  # Save proof for audit
  cp proof.json "proof-$(date +%s).json"
  
  # Execute terraform
  terraform apply -auto-approve
else
  echo "✗ Infrastructure change blocked by policy"
  exit 1
fi
```

## Use Case 3: Database Migration with Guard

Use the guard pattern for automatic rollback on denial:

```bash
#!/bin/bash

vigil guard \
  --agent-id migration-bot \
  --policy-id db-migration \
  -- ./run-migration.sh

if [ $? -ne 0 ]; then
  echo "Migration failed or was denied by policy"
  echo "Rolling back..."
  ./rollback-migration.sh
  exit 1
fi

echo "Migration completed with proof"
```

## Use Case 4: Kubernetes Operator

Gate operator decisions:

```python
import kopf
import subprocess
import hashlib
from kubernetes import client

@kopf.on.event('batch', 'v1', 'Job', annotations={'vigil/protect': 'true'})
def protect_job(event, name, namespace, **kwargs):
    """Gate job execution with Vigil proof."""
    
    job = event['object']
    job_spec = json.dumps(job['spec'], sort_keys=True)
    action_hash = f"sha256:{hashlib.sha256(job_spec.encode()).hexdigest()}"
    
    # Request proof
    result = subprocess.run([
        'vigil', 'prove',
        '--agent-id', 'k8s-operator',
        '--action-hash', action_hash,
        '--policy-id', f'k8s-{job[\"spec\"][\"template\"][\"metadata\"][\"labels\"][\"tier\"]}',
    ])
    
    if result.returncode != 0:
        # Deny the job
        kopf.patch(
            client.V1Job,
            name,
            namespace,
            body={'metadata': {'annotations': {'vigil/denied': 'true'}}}
        )
        raise kopf.PermanentError("Job execution denied by Vigil policy")
    
    # Job proceeds
    kopf.patch(
        client.V1Job,
        name,
        namespace,
        body={'metadata': {'annotations': {'vigil/approved': 'true'}}}
    )
```

## Use Case 5: Shell Script with Proof Verification

Save proofs for later verification:

```bash
#!/bin/bash

# Execute action and save proof
vigil prove \
  --agent-id backup-service \
  --action-hash "$(sha256sum backup.tar.gz | cut -d' ' -f1 | sed 's/^/sha256:/')" \
  --policy-id backup-approved \
  --json > backup-proof.json

if [ $? -ne 0 ]; then
  echo "Backup blocked"
  exit 1
fi

# Perform backup
tar czf backup-$(date +%s).tar.gz /data

# Verify proof can be checked later
vigil verify backup-proof.json
if [ $? -eq 0 ]; then
  echo "✓ Backup proof is valid"
else
  echo "✗ Backup proof compromised"
  exit 1
fi
```

## Use Case 6: CI/CD Pipeline with Status Checks

Monitor system health before deployments:

```yaml
# .github/workflows/deploy.yml

name: Deploy
on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      # Check if Vigil service is healthy
      - name: Check Vigil status
        env:
          VIGIL_ENDPOINT: https://proof.mycompany.com
        run: |
          vigil status --quiet || exit 1
          echo "✓ Vigil service is healthy"
      
      # Get approval via Vigil
      - name: Request deployment proof
        env:
          VIGIL_ENDPOINT: https://proof.mycompany.com
        run: |
          vigil prove \
            --agent-id github-actions \
            --action-hash "sha256:${{ github.sha }}" \
            --policy-id github-deploy \
            --json > deployment-proof.json
      
      # Deploy with proof
      - name: Deploy
        run: |
          vigil guard \
            --agent-id github-actions \
            --policy-id github-deploy \
            -- ./deploy.sh production
      
      # Archive proof
      - name: Save proof for audit
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: deployment-proofs
          path: deployment-proof.json
```

## Integration Patterns

### Pattern 1: Silent Proof (Exit Code Only)

When you only care about success/failure:

```bash
if vigil prove --agent-id bot --action-hash sha256:abc --policy-id safe --quiet; then
  perform_action
else
  log_denial
fi
```

### Pattern 2: Captured Proof (JSON)

When you need to store the proof for audit:

```bash
PROOF=$(vigil prove ... --json)
echo "$PROOF" | jq '.receipt_id' # Extract receipt ID
echo "$PROOF" > audit/proof-$(date +%s).json
```

### Pattern 3: Guard with Rollback

Execute command with automatic cleanup on failure:

```bash
vigil guard \
  --agent-id deployer \
  --policy-id production \
  -- bash -c '
    ./deploy.sh && \
    ./smoke-tests.sh || \
    { ./rollback.sh; exit 1; }
  '
```

### Pattern 4: Audit Trail

Monitor all actions through the system:

```bash
#!/bin/bash
while true; do
  ENTRIES=$(vigil status --json | jq '.entries | length')
  echo "$(date): $ENTRIES actions in audit log"
  
  # Alert if root changed unexpectedly
  CURRENT_ROOT=$(vigil status --json | jq -r '.merkle_root')
  if [ "$CURRENT_ROOT" != "$LAST_ROOT" ]; then
    echo "Audit log changed"
    vigil status --json | jq '.entries[-1]'  # Show latest
  fi
  
  LAST_ROOT=$CURRENT_ROOT
  sleep 60
done
```

## Environment Setup

### Local Development

```bash
# Start Vigil service
python main.py &

# Run agent with local service
export VIGIL_ENDPOINT=http://localhost:5000
python my_agent.py
```

### Production Deployment

```bash
# Configure service endpoint
export VIGIL_ENDPOINT=https://proof.mycompany.com

# Optional: project identifier
export VIGIL_PROJECT_ID=production

# Run agent/automation
./deploy-production.sh
```

## Error Handling

### Service Connection Errors

```bash
vigil prove ... 
# ✗ Proof failed: Connection refused

# Check endpoint
curl $VIGIL_ENDPOINT/health

# Fix endpoint if needed
export VIGIL_ENDPOINT=https://new-endpoint.com
```

### Policy Denials

```bash
vigil prove --policy-id dangerous ...
# ✗ Proof failed: Policy not found

# Check available policies via status
vigil status
```

### Invalid Receipts

```bash
vigil verify proof.json
# ✗ INVALID signature

# Proof may have been tampered with
# Request new proof instead
```

## Security Checklist

When integrating Vigil into your system:

- ✅ Use environment variables for endpoint (not hardcoded)
- ✅ Verify Vigil service TLS certificate in production
- ✅ Save proofs for audit trail
- ✅ Monitor policy denials and alert
- ✅ Use --quiet flag in automation (parse exit codes only)
- ✅ Use --json flag when saving proofs for audit
- ✅ Never override proof denial
- ✅ Regularly verify saved proofs still validate

## Debugging

### See what proof would look like

```bash
vigil prove ... --json | jq
```

### Check current system state

```bash
vigil status --json | jq '{root: .merkle_root, count: .entry_count}'
```

### Verify a saved proof

```bash
vigil verify proof.json
```

### Monitor proof requests in real-time

```bash
watch 'vigil status --json | jq .entry_count'
```

---

See [CLI.md](CLI.md) for full command reference.
