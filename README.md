# Vigil

**Black box recorder for AI agents. Cryptographically provable audit trails.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

Vigil creates tamper-proof, cryptographically signed records of every action your AI agent takes. When something goes wrong, you can prove exactly what happened.

```python
from vigil import sign_action

@sign_action
def trade_stock(ticker: str, shares: int, price: float):
    return execute_trade(ticker, shares, price)

# Every call automatically generates a cryptographic proof
# https://vigil.dev/proof/abc123def456
```

---

## Why Vigil?

**The Problem:**
- AI agents execute financial transactions, manage infrastructure, control systems
- When they make mistakes, you need proof of what actually happened
- Traditional logs can be edited, deleted, or forged
- "The agent hallucinated" vs "The API failed" — how do you know?

**The Solution:**
- Hardware-backed cryptographic signing (AWS Nitro Enclaves)
- Every agent action gets a tamper-proof timestamp and signature
- Publicly verifiable proof links
- Even root access can't forge or delete records

**In Practice:**
```python
# Agent executes action
result = trade_stock("AAPL", 100, 150.25)

# Vigil automatically creates proof
proof_url = "https://vigil.dev/proof/7f3a9e2b"

# Anyone can verify it happened
{
  "action": "trade_stock",
  "params": {"ticker": "AAPL", "shares": 100, "price": 150.25},
  "result": {"order_id": "ORD-12345", "status": "filled"},
  "timestamp": "2025-01-25T14:23:11Z",
  "signature": "ed25519:a8f3...",
  "verified": true
}
```

---

## Quick Start

### Installation

```bash
pip install vigil-sdk
```

### Basic Usage

```python
from vigil import sign_action

# Decorate any agent function
@sign_action
def send_email(to: str, subject: str, body: str):
    # Your agent logic here
    email_service.send(to, subject, body)
    return {"sent": True, "message_id": "msg-123"}

# Use it normally
result = send_email(
    to="user@example.com",
    subject="Order Confirmation", 
    body="Your order has shipped"
)

# Get the proof
print(result.vigil_proof_url)
# → https://vigil.dev/proof/8k2m5n9p
```

### Verification

Anyone can verify a proof:

```python
from vigil import verify_proof

proof = verify_proof("8k2m5n9p")
print(proof.verified)  # True
print(proof.timestamp)  # 2025-01-25T14:23:11Z
print(proof.action)     # "send_email"
```

Or visit the proof URL directly: `https://vigil.dev/proof/8k2m5n9p`

---

## Framework Integrations

### LangChain

```python
from langchain.agents import AgentExecutor
from vigil.integrations import VigilLangChain

# Wrap your agent
agent = AgentExecutor(...)
vigil_agent = VigilLangChain(agent)

# All tool calls are automatically signed
result = vigil_agent.run("Buy 100 shares of NVDA")
print(result.proof_url)
```

### AutoGPT

```python
from autogpt.agent import Agent
from vigil.integrations import VigilAutoGPT

agent = Agent(...)
vigil_agent = VigilAutoGPT(agent)

# Every command gets a proof
vigil_agent.run(["Write code", "Execute tests", "Deploy"])
```

### CrewAI

```python
from crewai import Agent, Task, Crew
from vigil.integrations import VigilCrew

crew = Crew(agents=[...], tasks=[...])
vigil_crew = VigilCrew(crew)

result = vigil_crew.kickoff()
# Access proofs for each task
for task in result.tasks:
    print(task.vigil_proof_url)
```

---

## Advanced Usage

### Batch Operations

```python
from vigil import VigilBatch

with VigilBatch() as batch:
    batch.sign(trade_stock("AAPL", 100, 150.25))
    batch.sign(trade_stock("GOOGL", 50, 2800.00))
    batch.sign(trade_stock("MSFT", 75, 380.50))

# Get single proof for entire batch
print(batch.proof_url)
```

### Custom Metadata

```python
@sign_action(metadata={
    "environment": "production",
    "user_id": "user_123",
    "risk_level": "high"
})
def execute_withdrawal(amount: float, account: str):
    return bank.withdraw(amount, account)
```

### Audit Trail Export

```python
from vigil import VigilClient

client = VigilClient(api_key="your_key")

# Export last 30 days of proofs
proofs = client.export_audit_trail(
    start_date="2025-01-01",
    end_date="2025-01-31",
    format="json"  # or "csv"
)
```

---

## Use Cases

### 🏦 Financial Services
**Problem:** Prove trading decisions weren't manipulated  
**Solution:** Every trade signed with hardware-backed keys

### 🤖 Autonomous Systems
**Problem:** Debug agent failures in production  
**Solution:** Unforgeable execution logs

### 🏥 Healthcare
**Problem:** Regulatory compliance for AI decisions  
**Solution:** Audit-ready proof of every patient interaction

### 🔐 Security Operations
**Problem:** Insider threat from privileged access  
**Solution:** Even root users can't forge agent actions

---

## How It Works

```
┌─────────────────┐
│  Your Agent     │
│  Function Call  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Vigil Decorator │
│ Captures I/O    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Nitro Enclave   │
│ Signs Action    │ ◄── Hardware-isolated
└────────┬────────┘     Private keys never leave
         │
         ▼
┌─────────────────┐
│ Merkle Tree     │
│ Immutable Log   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Proof URL       │
│ Public Verify   │
└─────────────────┘
```

**Key Properties:**
- ✅ **Tamper-proof:** Cryptographic signatures (Ed25519)
- ✅ **Verifiable:** Anyone can check validity
- ✅ **Unforgeable:** Hardware-backed signing keys
- ✅ **Immutable:** Merkle tree prevents deletion
- ✅ **Timestamped:** Exact execution time

---

## API Reference

### `@sign_action`

Decorator for signing agent functions.

```python
@sign_action(
    metadata: dict = None,      # Custom key-value pairs
    include_result: bool = True, # Sign return value
    include_params: bool = True  # Sign input parameters
)
```

### `verify_proof(proof_id: str)`

Verify a proof's authenticity.

**Returns:**
```python
{
    "verified": bool,
    "action": str,
    "timestamp": str,
    "signature": str,
    "params": dict,
    "result": dict,
    "metadata": dict
}
```

### `VigilClient`

Programmatic access to Vigil API.

```python
client = VigilClient(
    api_key="vigil_sk_...",
    environment="production"  # or "staging"
)

# Create proof
proof = client.create_proof(
    action="custom_action",
    data={"key": "value"}
)

# List proofs
proofs = client.list_proofs(limit=100)

# Export audit trail
trail = client.export_audit_trail(
    start_date="2025-01-01",
    end_date="2025-01-31"
)
```

---

## Configuration

### Environment Variables

```bash
# Required
VIGIL_API_KEY=vigil_sk_xxxxx

# Optional
VIGIL_ENVIRONMENT=production  # or staging
VIGIL_ENDPOINT=https://api.vigil.dev
VIGIL_AUTO_VERIFY=true        # Verify after signing
```

### Config File

Create `vigil.config.json`:

```json
{
  "api_key": "vigil_sk_xxxxx",
  "environment": "production",
  "auto_verify": true,
  "metadata": {
    "team": "trading",
    "region": "us-east-1"
  }
}
```

---

## Examples

See the [`examples/`](./examples) directory:

- **[Basic Trading Bot](./examples/trading_bot.py)** - Simple stock trading with proofs
- **[LangChain Integration](./examples/langchain_agent.py)** - Customer service agent
- **[Batch Processing](./examples/batch_operations.py)** - Bulk email sender
- **[Custom Verification](./examples/custom_verify.py)** - Build your own proof checker
- **[Audit Export](./examples/export_trail.py)** - Generate compliance reports

---

## Security

### Threat Model

**What Vigil Protects Against:**
- ✅ Insider tampering (even with root access)
- ✅ Log deletion or modification
- ✅ Timestamp manipulation
- ✅ Action forgery or impersonation

**What Vigil Doesn't Protect Against:**
- ❌ Compromised application logic (garbage in, garbage out)
- ❌ Stolen API keys (rotate keys immediately)
- ❌ Side-channel attacks on the host

### Best Practices

```python
# ✅ DO: Sign high-risk actions
@sign_action
def execute_payment(amount, recipient):
    return payment_gateway.transfer(amount, recipient)

# ✅ DO: Include user context
@sign_action(metadata={"user_id": current_user.id})
def delete_database(database_name):
    return db.drop(database_name)

# ❌ DON'T: Sign every trivial action
@sign_action  # Overkill for logging
def log_message(msg):
    print(msg)
```


## FAQ

**Q: How is this different from logging?**  
A: Logs can be edited or deleted. Vigil proofs are cryptographically signed and stored in an immutable Merkle tree. Even with root access, tampering is impossible.

**Q: Do I need AWS to use Vigil?**  
A: No. We run the signing infrastructure. You just call our API. (Enterprise customers can self-host in their own enclaves.)

**Q: What if Vigil goes down?**  
A: Your agent continues working normally. Proofs are queued and signed when service resumes. Zero downtime for your operations.

**Q: Can I verify proofs offline?**  
A: Yes. Download the public key and Merkle root, then verify signatures locally.

**Q: How much does signing slow down my agent?**  
A: ~10-50ms per action. Async mode available for latency-sensitive operations.

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md).

```bash
# Clone repo
git clone https://github.com/rom-mvp/vigil-cryptographicsign
cd vigil-cryptographicsign

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Submit PR
```

---

## License

MIT License - see [LICENSE](./LICENSE) for details.

---

## Built With Vigil

---

<p align="center">
  <strong>Vigil:</strong> The trust layer for autonomous systems.
  <br>
