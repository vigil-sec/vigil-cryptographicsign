# UNTRUSTED CLI CODE
# 'prove' command - Request a cryptographic proof before action

import json
import sys
from typing import Optional
from ..client import VigilClient


def prove(
    endpoint: str,
    agent_id: str,
    action_hash: str,
    policy_id: str,
    json_output: bool = False,
    quiet: bool = False
) -> int:
    """
    Request a cryptographic proof for an agent action.
    
    Args:
        endpoint: Vigil service endpoint
        agent_id: ID of the agent performing the action
        action_hash: SHA256 hash of the action
        policy_id: Policy ID governing this action
        json_output: Output as JSON only
        quiet: Suppress output, return exit code only
    
    Returns:
        Exit code: 0 on success, 1 on failure
    """
    client = VigilClient(endpoint)
    
    try:
        # Request proof from service
        receipt = client.prove(agent_id, action_hash, policy_id)
        
        # Print result
        if not quiet:
            if json_output:
                print(json.dumps(receipt, indent=2))
            else:
                print(f"✓ Proof granted")
                print(f"  Receipt ID: {receipt.get('receipt_id')}")
                print(f"  Agent: {receipt.get('agent_id')}")
                print(f"  Policy: {receipt.get('policy_id')}")
                print(f"  Merkle Root: {receipt.get('merkle_root', '')[:16]}...")
                print(f"  Timestamp: {receipt.get('timestamp')}")
        
        return 0
    
    except Exception as e:
        if not quiet:
            print(f"✗ Proof failed: {str(e)}", file=sys.stderr)
        return 1
