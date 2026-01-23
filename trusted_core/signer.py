# THIS MOVES INTO ENCLAVE
# Signer - Core signing logic with audit log enforcement

import time
from typing import Optional
from .key_manager import KeyManager
from .audit_log import AuditLog
from .execution_receipt import ExecutionReceipt


class Signer:
    """
    Core signing service for the trusted core.
    
    Enforces the critical security invariant: NO LOG = NO SIGNATURE
    
    The signer:
    1. Accepts a proof request (agent_id, action_hash, policy_id)
    2. Appends to the audit log FIRST
    3. Only then signs the receipt with the audit log's Merkle root
    
    This makes every signature cryptographically bound to the audit log,
    making log tampering immediately detectable.
    """
    
    def __init__(self, key_manager: KeyManager, audit_log: AuditLog):
        """
        Initialize the signer.
        
        Args:
            key_manager: Enclave key manager
            audit_log: Append-only audit log
        """
        self.key_manager = key_manager
        self.audit_log = audit_log
        self.receipt_counter = 0
    
    def prove(self, agent_id: str, action_hash: str, policy_id: str) -> ExecutionReceipt:
        """
        Prove an agent action and return a signed receipt.
        
        Security flow:
        1. Append to audit log (BEFORE signing)
        2. Get Merkle root from log
        3. Sign the receipt with Ed25519
        4. Return receipt
        
        Args:
            agent_id: ID of the agent
            action_hash: SHA256 hash of the action
            policy_id: Policy ID
        
        Returns:
            ExecutionReceipt with cryptographic proof
        """
        timestamp = int(time.time())
        
        # CRITICAL: Append to audit log FIRST
        # This ensures every signature is bound to the log
        log_entry = self.audit_log.append(agent_id, action_hash, policy_id, timestamp)
        
        # Get the Merkle root after appending
        merkle_root = self.audit_log.get_root()
        
        # Create receipt
        self.receipt_counter += 1
        receipt = ExecutionReceipt(
            receipt_id=f"receipt-{self.receipt_counter:06d}",
            agent_id=agent_id,
            action_hash=action_hash,
            policy_id=policy_id,
            merkle_root=merkle_root,
            timestamp=timestamp,
            signature=""  # Will be filled in
        )
        
        # Sign the receipt
        signature_bytes = self._sign_receipt(receipt)
        receipt.signature = signature_bytes.hex()
        
        return receipt
    
    def _sign_receipt(self, receipt: ExecutionReceipt) -> bytes:
        """
        Sign the receipt payload with the private key.
        
        Args:
            receipt: ExecutionReceipt to sign
        
        Returns:
            Raw signature bytes
        """
        # Get the bytes that should be signed
        payload = receipt.get_signed_payload()
        
        # Sign with Ed25519 private key (ENCLAVE-ONLY)
        private_key = self.key_manager.get_private_key()
        signature = private_key.sign(payload)
        
        return signature
    
    def verify_receipt(self, receipt: ExecutionReceipt) -> bool:
        """
        Verify a receipt signature.
        
        This can be called from the host to verify receipts.
        
        Args:
            receipt: ExecutionReceipt to verify
        
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            payload = receipt.get_signed_payload()
            signature_bytes = bytes.fromhex(receipt.signature)
            
            public_key = self.key_manager.get_public_key()
            public_key.verify(signature_bytes, payload)
            
            return True
        except Exception:
            return False
