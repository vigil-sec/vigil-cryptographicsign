# Main entry point for the Vigil MVP

import logging
from trusted_core import KeyManager, AuditLog, Signer
from host import HostAPI


def main():
    """
    Initialize and run the Vigil MVP.
    
    Architecture:
    - trusted_core components initialize with simulated enclave properties
    - Host API spins up and communicates with trusted_core
    - In production, trusted_core would be in a Nitro Enclave
    """
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("Vigil: Hardware-Backed Trust System for AI Agents")
    logger.info("MVP v0.1 - Software-only prototype")
    logger.info("=" * 60)
    
    # Initialize trusted_core components
    logger.info("\n[TRUSTED CORE] Initializing enclave components...")
    key_manager = KeyManager()
    logger.info("  ✓ Ed25519 signing key initialized (sealed)")
    
    audit_log = AuditLog()
    logger.info("  ✓ Audit log initialized")
    
    signer = Signer(key_manager, audit_log)
    logger.info("  ✓ Signer service ready")
    
    # Get public key for verification
    public_key_pem = key_manager.get_public_key_pem()
    logger.info("\n[PUBLIC KEY] (safe to export)")
    logger.info("-" * 60)
    logger.info(public_key_pem)
    logger.info("-" * 60)
    
    # Initialize host API
    logger.info("\n[HOST API] Starting REST server...")
    
    # Respect PORT environment variable
    import os
    port = int(os.getenv("PORT", 5000))
    api = HostAPI(signer, port=port)
    
    logger.info("\n" + "=" * 60)
    logger.info(f"READY - API listening on http://localhost:{port}")
    logger.info("=" * 60)
    logger.info("\nTry:")
    logger.info(f'  curl -X POST http://localhost:{port}/prove \\')
    logger.info('    -H "Content-Type: application/json" \\')
    logger.info('    -d \'{')
    logger.info('      "agent_id": "agent-42",')
    logger.info('      "action_hash": "sha256:abc123...",')
    logger.info('      "policy_id": "policy-default"')
    logger.info('    }\'')
    logger.info("\nOr check audit log:")
    logger.info(f'  curl http://localhost:{port}/audit-log')
    logger.info("=" * 60 + "\n")
    
    # Start the API server (blocking)
    api.run(debug=False)


if __name__ == '__main__':
    main()
