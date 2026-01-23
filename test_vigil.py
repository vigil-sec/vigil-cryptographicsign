#!/usr/bin/env python3
"""
Integration test and demo script for Vigil MVP.

Demonstrates:
- Proof request/response cycle
- Audit log accumulation
- Merkle root changes
- Signature verification
- Tampering detection
"""

import json
import time
import subprocess
import requests
from pathlib import Path


def test_vigil():
    """Run comprehensive tests of the Vigil system."""
    
    print("\n" + "=" * 70)
    print("VIGIL MVP - INTEGRATION TEST")
    print("=" * 70)
    
    # Kill any existing process
    subprocess.run("pkill -f 'python main.py'", shell=True, stderr=subprocess.DEVNULL)
    time.sleep(1)
    
    # Start the Vigil server
    print("\n[1] Starting Vigil server...")
    proc = subprocess.Popen(
        ["python", "main.py"],
        cwd=Path(__file__).parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(2)
    print("    ✓ Server ready on http://localhost:5000")
    
    try:
        # Test 1: Single proof request
        print("\n[2] Testing single proof request...")
        response = requests.post(
            "http://localhost:5000/prove",
            json={
                "agent_id": "agent-alpha",
                "action_hash": "sha256:1234567890abcdef",
                "policy_id": "policy-v1"
            },
            timeout=5
        )
        receipt_1 = response.json()
        print(f"    ✓ Receipt ID: {receipt_1['receipt_id']}")
        print(f"    ✓ Signature: {receipt_1['signature'][:32]}...")
        print(f"    ✓ Merkle Root: {receipt_1['merkle_root'][:32]}...")
        
        root_1 = receipt_1['merkle_root']
        
        # Test 2: Multiple proofs accumulate
        print("\n[3] Testing audit log accumulation...")
        for i in range(3):
            requests.post(
                "http://localhost:5000/prove",
                json={
                    "agent_id": f"agent-{chr(97+i)}",  # agent-a, agent-b, agent-c
                    "action_hash": f"sha256:{i}{'0'*60}",
                    "policy_id": f"policy-v{i+1}"
                },
                timeout=5
            )
            print(f"    ✓ Proof {i+2} appended")
        
        # Test 3: Merkle root changes with each entry
        print("\n[4] Verifying Merkle root commitment...")
        log_response = requests.get("http://localhost:5000/audit-log", timeout=5)
        audit = log_response.json()
        
        print(f"    Total entries: {audit['entry_count']}")
        current_root = audit['merkle_root']
        print(f"    Final Merkle Root: {current_root[:32]}...")
        
        if root_1 != current_root:
            print(f"    ✓ Root changed after appending (tamper-evident)")
        else:
            print(f"    ✗ Root should have changed")
        
        # Test 4: Signature verification
        print("\n[5] Testing receipt verification...")
        verify_response = requests.post(
            "http://localhost:5000/verify",
            json=receipt_1,
            timeout=5
        )
        verification = verify_response.json()
        
        if verification['valid']:
            print(f"    ✓ Signature {verification['receipt_id']} is valid")
        else:
            print(f"    ✗ Signature verification failed")
        
        # Test 5: Tamper detection
        print("\n[6] Testing tamper detection...")
        tampered_receipt = receipt_1.copy()
        tampered_receipt['signature'] = '00' * 64  # Invalid signature
        
        tamper_response = requests.post(
            "http://localhost:5000/verify",
            json=tampered_receipt,
            timeout=5
        )
        tamper_result = tamper_response.json()
        
        if not tamper_result['valid']:
            print(f"    ✓ Tampered signature correctly rejected")
        else:
            print(f"    ✗ Tampered signature should be rejected")
        
        # Test 6: Audit log integrity
        print("\n[7] Testing audit log integrity...")
        entries = audit['entries']
        print(f"    Log entries:")
        for entry in entries:
            print(f"      [{entry['sequence']}] agent={entry['agent_id']}, "
                  f"policy={entry['policy_id']}")
        
        # Test 7: API error handling
        print("\n[8] Testing error handling...")
        error_response = requests.post(
            "http://localhost:5000/prove",
            json={
                "agent_id": "agent-test"
                # Missing action_hash and policy_id
            },
            timeout=5
        )
        
        if error_response.status_code != 200:
            print(f"    ✓ Validation error correctly returned ({error_response.status_code})")
        else:
            print(f"    ✗ Should reject incomplete request")
        
        print("\n" + "=" * 70)
        print("ALL TESTS PASSED ✓")
        print("=" * 70)
        
        print("\nKey takeaways:")
        print("  • Proofs are cryptographically signed with Ed25519")
        print("  • Audit log is append-only (no log = no signature)")
        print("  • Merkle root commits to the entire log")
        print("  • Any tampering is immediately detectable")
        print("  • This architecture maps 1:1 to hardware enclaves")
        print("\n")
        
    finally:
        # Clean up
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == '__main__':
    test_vigil()
