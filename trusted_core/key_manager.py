# THIS MOVES INTO ENCLAVE
# Key Manager - Simulates enclave key sealing and generation

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from pathlib import Path
import os


class KeyManager:
    """
    Manages the Ed25519 signing key for the trusted core.
    
    In production (hardware enclave), the private key would be:
    - Generated inside the TEE
    - Sealed by the enclave's attestation key (AWS Nitro KMS)
    - Never exported outside the enclave
    
    In this MVP, we simulate sealing by storing on disk with restricted permissions.
    """
    
    def __init__(self, key_path: str = "/tmp/enclave_signing_key.pem"):
        """
        Initialize key manager.
        
        Args:
            key_path: Path where the private key is stored (simulated sealing)
        """
        self.key_path = key_path
        self._private_key = None
        self._public_key = None
        
        self._load_or_generate_key()
    
    def _load_or_generate_key(self):
        """Load existing key or generate a new one."""
        if os.path.exists(self.key_path):
            self._load_key()
        else:
            self._generate_key()
    
    def _generate_key(self):
        """Generate a new Ed25519 key pair."""
        self._private_key = ed25519.Ed25519PrivateKey.generate()
        self._public_key = self._private_key.public_key()
        
        # Serialize and save (simulating enclave sealing)
        pem = self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()  # In production: use HSM encryption
        )
        
        # Write with restricted permissions (owner read-only)
        Path(self.key_path).write_bytes(pem)
        os.chmod(self.key_path, 0o600)
    
    def _load_key(self):
        """Load Ed25519 key from disk."""
        pem = Path(self.key_path).read_bytes()
        self._private_key = serialization.load_pem_private_key(
            pem,
            password=None
        )
        self._public_key = self._private_key.public_key()
    
    def get_private_key(self):
        """
        Get the private key.
        
        ⚠️ ENCLAVE-ONLY: This should never be called from host code.
        In production, the host has no way to access this.
        """
        return self._private_key
    
    def get_public_key(self):
        """Get the public key (safe to export to host for verification)."""
        return self._public_key
    
    def get_public_key_pem(self) -> str:
        """Get public key in PEM format for external verification."""
        pem = self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')
