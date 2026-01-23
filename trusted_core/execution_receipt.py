# THIS MOVES INTO ENCLAVE
# Execution Receipt - Structured proof output from trusted core

from dataclasses import dataclass, asdict
from typing import Optional
import json


@dataclass
class ExecutionReceipt:
    """
    Signed proof of an AI agent action execution.
    
    This receipt is the output of the trusted_core signing process.
    Each field is included in the signature, making the receipt tamper-evident.
    """
    receipt_id: str              # Unique identifier for this receipt
    agent_id: str                # ID of the agent that performed the action
    action_hash: str             # SHA256 hash of the action payload
    policy_id: str               # Policy identifier governing this action
    merkle_root: str             # Merkle root of the audit log at signing time
    timestamp: int               # Unix timestamp of signature
    signature: str               # Ed25519 signature (hex-encoded)
    
    def to_dict(self) -> dict:
        """Convert receipt to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert receipt to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def get_signed_payload(self) -> bytes:
        """
        Return the exact bytes that were signed.
        
        Used for external verification. The order matters for reproducibility.
        """
        payload = f"{self.agent_id}|{self.action_hash}|{self.policy_id}|{self.merkle_root}|{self.timestamp}"
        return payload.encode('utf-8')
