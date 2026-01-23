# UNTRUSTED CLI CODE
# 'verify' command - Verify an execution receipt offline

import json
import sys
from pathlib import Path
from typing import Optional
from ..client import VigilClient


def verify(
    endpoint: str,
    receipt_file: str,
    quiet: bool = False
) -> int:
    """
    Verify an execution receipt signature.
    
    Args:
        endpoint: Vigil service endpoint
        receipt_file: Path to receipt JSON file
        quiet: Suppress output, return exit code only
    
    Returns:
        Exit code: 0 if valid, 1 if invalid
    """
    client = VigilClient(endpoint)
    
    try:
        # Load receipt from file
        receipt_path = Path(receipt_file)
        if not receipt_path.exists():
            if not quiet:
                print(f"✗ Receipt file not found: {receipt_file}", file=sys.stderr)
            return 1
        
        with open(receipt_path) as f:
            receipt = json.load(f)
        
        # Verify signature via service
        result = client.verify(receipt)
        
        if result.get('valid'):
            if not quiet:
                print(f"✓ VALID signature")
                print(f"  Receipt ID: {result.get('receipt_id')}")
            return 0
        else:
            if not quiet:
                print(f"✗ INVALID signature", file=sys.stderr)
                print(f"  Receipt ID: {result.get('receipt_id')}", file=sys.stderr)
            return 1
    
    except json.JSONDecodeError as e:
        if not quiet:
            print(f"✗ Invalid JSON in receipt file: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        if not quiet:
            print(f"✗ Verification failed: {str(e)}", file=sys.stderr)
        return 1
