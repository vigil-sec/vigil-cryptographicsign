#!/usr/bin/env python3
# UNTRUSTED CLI CODE
# Vigil CLI - Control surface for cryptographic proof service

import os
import sys
import argparse
from . import __version__
from .commands import prove as prove_cmd
from .commands import verify as verify_cmd
from .commands import status as status_cmd
from .commands import guard as guard_cmd


# TRUST LIVES SERVER-SIDE
# This CLI is an untrusted wrapper that:
# - Accepts user commands
# - Makes HTTP calls to the proof service
# - Returns structured responses
# - NEVER performs cryptography
# - NEVER holds private keys
# - NEVER signs anything


def get_endpoint() -> str:
    """Get the Vigil service endpoint from environment or default."""
    return os.environ.get('VIGIL_ENDPOINT', 'http://localhost:5000')


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        prog='vigil',
        description='Cryptographic proof service for AI agents',
        epilog='''
Examples:
  vigil prove --agent-id agent-1 --action-hash sha256:abc123 --policy-id prod-safe
  vigil verify receipt.json
  vigil status
  vigil guard --agent-id deployer --policy-id prod-safe -- terraform apply

For help on a specific command:
  vigil <command> --help

Environment:
  VIGIL_ENDPOINT   Service endpoint (default: http://localhost:5000)
  VIGIL_PROJECT_ID Optional project identifier
        '''
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # ========== PROVE COMMAND ==========
    prove_parser = subparsers.add_parser(
        'prove',
        help='Request a cryptographic proof before action'
    )
    prove_parser.add_argument(
        '--agent-id',
        required=True,
        help='ID of the agent performing the action'
    )
    prove_parser.add_argument(
        '--action-hash',
        required=True,
        help='SHA256 hash of the action (format: sha256:...)'
    )
    prove_parser.add_argument(
        '--policy-id',
        required=True,
        help='Policy ID governing this action'
    )
    prove_parser.add_argument(
        '--json',
        action='store_true',
        help='Output as machine-readable JSON'
    )
    prove_parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress output, exit code only'
    )
    
    # ========== VERIFY COMMAND ==========
    verify_parser = subparsers.add_parser(
        'verify',
        help='Verify an execution receipt'
    )
    verify_parser.add_argument(
        'receipt',
        help='Path to receipt JSON file'
    )
    verify_parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress output, exit code only'
    )
    
    # ========== STATUS COMMAND ==========
    status_parser = subparsers.add_parser(
        'status',
        help='Read-only system monitoring'
    )
    status_parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )
    status_parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress output'
    )
    
    # ========== GUARD COMMAND ==========
    guard_parser = subparsers.add_parser(
        'guard',
        help='Gate command execution with proof requirement'
    )
    guard_parser.add_argument(
        '--agent-id',
        required=True,
        help='ID of the agent requesting execution'
    )
    guard_parser.add_argument(
        '--policy-id',
        required=True,
        help='Policy ID for execution'
    )
    guard_parser.add_argument(
        '--json',
        action='store_true',
        help='Output proof as JSON'
    )
    guard_parser.add_argument(
        'cmd',
        nargs='*',
        help='Command to execute (use -- to separate from vigil args)'
    )
    
    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Get service endpoint
    endpoint = get_endpoint()
    
    # Dispatch to command
    if args.command == 'prove':
        exit_code = prove_cmd.prove(
            endpoint=endpoint,
            agent_id=args.agent_id,
            action_hash=args.action_hash,
            policy_id=args.policy_id,
            json_output=args.json,
            quiet=args.quiet
        )
    
    elif args.command == 'verify':
        exit_code = verify_cmd.verify(
            endpoint=endpoint,
            receipt_file=args.receipt,
            quiet=args.quiet
        )
    
    elif args.command == 'status':
        exit_code = status_cmd.status(
            endpoint=endpoint,
            json_output=args.json,
            quiet=args.quiet
        )
    
    elif args.command == 'guard':
        exit_code = guard_cmd.guard(
            endpoint=endpoint,
            agent_id=args.agent_id,
            policy_id=args.policy_id,
            command=args.cmd if hasattr(args, 'cmd') and args.cmd else [],
            json_output=args.json
        )
    
    else:
        parser.print_help()
        exit_code = 0
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
