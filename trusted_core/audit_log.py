# THIS MOVES INTO ENCLAVE
# Audit Log - Append-only log with Merkle tree commitment

import hashlib
import json
from datetime import datetime
from typing import List
from dataclasses import dataclass, asdict


@dataclass
class LogEntry:
    """Single entry in the append-only audit log."""
    sequence: int               # Entry number (monotonically increasing)
    timestamp: int              # Unix timestamp when entry was appended
    agent_id: str               # Agent that triggered the action
    action_hash: str            # SHA256 of the action
    policy_id: str              # Policy ID
    merkle_root_after: str      # Merkle root AFTER this entry is added
    
    def to_bytes(self) -> bytes:
        """Serialize for hashing."""
        data = f"{self.sequence}|{self.timestamp}|{self.agent_id}|{self.action_hash}|{self.policy_id}"
        return data.encode('utf-8')


class AuditLog:
    """
    Append-only audit log with Merkle tree proofs.
    
    Properties:
    - Entries can only be appended, never modified or deleted
    - Merkle root changes if any entry is modified (tamper-evident)
    - Used to enforce "no log = no signature"
    """
    
    def __init__(self):
        """Initialize empty audit log."""
        self.entries: List[LogEntry] = []
        self.sequence_counter = 0
        self.merkle_root = self._compute_root()
    
    def append(self, agent_id: str, action_hash: str, policy_id: str, timestamp: int) -> LogEntry:
        """
        Append a new entry to the audit log.
        
        Args:
            agent_id: Agent identifier
            action_hash: SHA256 hash of the action
            policy_id: Policy identifier
            timestamp: Unix timestamp
        
        Returns:
            The new LogEntry
        """
        self.sequence_counter += 1
        
        # Create entry (merkle_root_after will be filled in)
        entry = LogEntry(
            sequence=self.sequence_counter,
            timestamp=timestamp,
            agent_id=agent_id,
            action_hash=action_hash,
            policy_id=policy_id,
            merkle_root_after=""  # Placeholder
        )
        
        # Append to log
        self.entries.append(entry)
        
        # Recompute merkle root
        self.merkle_root = self._compute_root()
        
        # Update entry with new root
        entry.merkle_root_after = self.merkle_root
        
        return entry
    
    def _compute_root(self) -> str:
        """
        Compute the Merkle root of all entries.
        
        Uses SHA256 hash tree. If any entry is modified, the root changes.
        This makes tampering immediately detectable.
        """
        if not self.entries:
            # Root of empty log is hash of "empty"
            return hashlib.sha256(b"empty").hexdigest()
        
        # Create leaf hashes
        leaves = [hashlib.sha256(entry.to_bytes()).digest() for entry in self.entries]
        
        # Build tree bottom-up
        while len(leaves) > 1:
            # If odd number of leaves, duplicate the last one
            if len(leaves) % 2 == 1:
                leaves.append(leaves[-1])
            
            # Hash pairs
            parents = []
            for i in range(0, len(leaves), 2):
                parent = hashlib.sha256(leaves[i] + leaves[i+1]).digest()
                parents.append(parent)
            leaves = parents
        
        # Return root as hex string
        return leaves[0].hex()
    
    def get_root(self) -> str:
        """Get the current Merkle root."""
        return self.merkle_root
    
    def get_entries(self) -> List[dict]:
        """Get all entries as dictionaries."""
        return [asdict(entry) for entry in self.entries]
    
    def get_entry_count(self) -> int:
        """Get the number of entries in the log."""
        return len(self.entries)
    
    def verify_tamper_free(self) -> bool:
        """
        Verify that the log hasn't been tampered with.
        
        Recomputes the Merkle root and compares with stored value.
        Returns True if they match, False if tampering is detected.
        """
        computed_root = self._compute_root()
        return computed_root == self.merkle_root
