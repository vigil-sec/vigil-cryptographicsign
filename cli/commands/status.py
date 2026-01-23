# UNTRUSTED CLI CODE
# 'status' command - Read-only system monitoring

import json
import sys
from ..client import VigilClient


def status(
    endpoint: str,
    json_output: bool = False,
    quiet: bool = False
) -> int:
    """
    Get the current system status.
    
    Reads the audit log to show:
    - Current Merkle root
    - Number of entries
    - Recent activity
    
    This is READ-ONLY and does not mutate state.
    
    Args:
        endpoint: Vigil service endpoint
        json_output: Output as JSON
        quiet: Suppress output
    
    Returns:
        Exit code: 0 on success, 1 on failure
    """
    client = VigilClient(endpoint)
    
    try:
        # Get audit log
        audit = client.get_audit_log()
        
        if json_output:
            print(json.dumps(audit, indent=2))
        elif not quiet:
            print(f"✓ System Status")
            print(f"  Merkle Root: {audit.get('merkle_root', '')[:32]}...")
            print(f"  Entry Count: {audit.get('entry_count', 0)}")
            
            # Show recent entries
            entries = audit.get('entries', [])
            if entries:
                print(f"\n  Recent Entries:")
                for entry in entries[-3:]:  # Last 3 entries
                    print(f"    [{entry['sequence']}] agent={entry['agent_id']}, "
                          f"policy={entry['policy_id']}")
        
        return 0
    
    except Exception as e:
        if not quiet:
            print(f"✗ Status check failed: {str(e)}", file=sys.stderr)
        return 1
