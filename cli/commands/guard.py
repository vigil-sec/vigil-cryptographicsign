# UNTRUSTED CLI CODE
# 'guard' command - Gate command execution with proof requirement

import json
import sys
import subprocess
import hashlib
from typing import List
from ..client import VigilClient


def guard(
    endpoint: str,
    agent_id: str,
    policy_id: str,
    command: List[str],
    json_output: bool = False
) -> int:
    """
    Execute a command only if a cryptographic proof can be obtained.
    
    Flow:
    1. Compute hash of the command
    2. Request proof via vigil prove
    3. If proof succeeds, execute command
    4. If proof fails, block execution (exit 1)
    
    Args:
        endpoint: Vigil service endpoint
        agent_id: Agent requesting execution
        policy_id: Policy to enforce
        command: Command to execute (list of arguments)
        json_output: Output proof as JSON on success
    
    Returns:
        Exit code: Proof success (0/1) if proof fails, command exit code if succeeds
    """
    client = VigilClient(endpoint)
    
    if not command:
        print("✗ No command provided", file=sys.stderr)
        return 1
    
    try:
        # Compute hash of command
        command_str = ' '.join(command)
        action_hash = hashlib.sha256(command_str.encode()).hexdigest()
        action_hash = f"sha256:{action_hash}"
        
        # Request proof
        receipt = client.prove(agent_id, action_hash, policy_id)
        
        # Proof succeeded - now execute the command
        print(f"✓ Proof granted for: {command_str}", file=sys.stderr)
        if json_output:
            print(json.dumps(receipt, indent=2))
            print("", file=sys.stderr)  # Blank line before command output
        
        # Execute command
        result = subprocess.run(command)
        return result.returncode
    
    except Exception as e:
        print(f"✗ Guard denied: {str(e)}", file=sys.stderr)
        return 1
