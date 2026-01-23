#!/usr/bin/env python3
"""
Example: Verifying a Vigil receipt offline.

This demonstrates how an external party can verify a receipt
without needing access to the private key or the signer.

Uses only the public key and the receipt.
"""

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import sys
import json


def verify_receipt_offline(receipt_json: str, public_key_pem: str) -> bool:
    """
    Verify a receipt signature using only public key and receipt data.
    
    Args:
        receipt_json: JSON string containing the receipt
        public_key_pem: PEM-encoded Ed25519 public key
    
    Returns:
        True if signature is valid, False otherwise
    """
    # Parse receipt
    receipt = json.loads(receipt_json)
    
    # Load public key
    public_key = serialization.load_pem_public_key(
        public_key_pem.encode('utf-8'),
        backend=default_backend()
    )
    
    # Reconstruct the signed payload (MUST match exact order)
    payload = (
        f"{receipt['agent_id']}|"
        f"{receipt['action_hash']}|"
        f"{receipt['policy_id']}|"
        f"{receipt['merkle_root']}|"
        f"{receipt['timestamp']}"
    ).encode('utf-8')
    
    # Decode signature from hex
    signature_bytes = bytes.fromhex(receipt['signature'])
    
    # Verify
    try:
        public_key.verify(signature_bytes, payload)
        return True
    except Exception as e:
        print(f"Verification failed: {e}", file=sys.stderr)
        return False


if __name__ == '__main__':
    # Example receipt from the system
    example_receipt = {
        "receipt_id": "receipt-000001",
        "agent_id": "agent-42",
        "action_hash": "sha256:abc123def456",
        "policy_id": "policy-default",
        "merkle_root": "79ae3195d57b7cef5e478a998f260040c4c716f8ae8a49be636e9c852c8af692",
        "timestamp": 1769189155,
        "signature": "cd0af9999efe8b33d8310c251d565ad66b4a4d2e04ddb26bc4f3fd58bea9657d819d6c6a9c6242ca60cfd500c4314d01e4b15310f43f475ab7991b5a7a711c05"
    }
    
    # The public key (exported from the signer)
    example_public_key = """-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEA2KIfWf2jnT7j/EkiZjuyYAlund4FFVtTlRYKHTLI7d4=
-----END PUBLIC KEY-----"""
    
    print("Example: Offline Receipt Verification")
    print("=" * 50)
    print("\nReceipt:")
    print(json.dumps(example_receipt, indent=2))
    print("\nPublic Key:")
    print(example_public_key)
    print("\nVerifying signature...")
    
    is_valid = verify_receipt_offline(
        json.dumps(example_receipt),
        example_public_key
    )
    
    if is_valid:
        print("✓ Signature is VALID")
        print("\nThe following can be cryptographically trusted:")
        print(f"  • Agent ID: {example_receipt['agent_id']}")
        print(f"  • Action: {example_receipt['action_hash']}")
        print(f"  • Policy: {example_receipt['policy_id']}")
        print(f"  • Merkle Root: {example_receipt['merkle_root'][:32]}...")
        print(f"  • Timestamp: {example_receipt['timestamp']}")
    else:
        print("✗ Signature is INVALID (receipt was tampered with)")
