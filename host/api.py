# UNTRUSTED HOST CODE
# Host API - REST endpoint for proving agent actions

from flask import Flask, jsonify, request
from typing import Optional
import logging

# Import trusted core (would be remote in hardware setup)
from trusted_core import Signer, ExecutionReceipt

logger = logging.getLogger(__name__)

# Create Flask app at module level
app = Flask(__name__)


# Helper to ensure requests are allowed (MVP: allow all)
def allow_request():
    """MVP: Allow all requests. Future: Add policy checks here."""
    return True


def setup_routes(signer: Signer):
    """Setup Flask routes.
    
    Args:
        signer: Reference to trusted_core signer
    """
    # Add before_request hook to explicitly allow all requests (MVP)
    @app.before_request
    def before_request():
        """Pre-request hook: MVP allows all. Future: Add policy enforcement."""
        if not allow_request():
            return jsonify({"error": "Request denied"}), 403
        return None
    
    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint."""
        return jsonify({"status": "ok"}), 200
    
    @app.route('/prove', methods=['POST'])
    def prove():
        """
        Prove an agent action.
        
        Request body:
        {
            "agent_id": "agent-42",
            "action_hash": "sha256:abc123...",
            "policy_id": "policy-default"
        }
        
        Returns:
        ExecutionReceipt (signed by trusted_core)
        """
        try:
            data = request.get_json()
            
            # Validate input (UNTRUSTED: always validate host input)
            if not data:
                return jsonify({"error": "No JSON body"}), 400
            
            agent_id = data.get('agent_id')
            action_hash = data.get('action_hash')
            policy_id = data.get('policy_id')
            
            # Basic validation
            if not agent_id or not action_hash or not policy_id:
                return jsonify({
                    "error": "Missing required fields: agent_id, action_hash, policy_id"
                }), 400
            
            # Request proof from trusted_core
            # (In this MVP, signer is in-process; in Nitro it would be RPC)
            receipt = signer.prove(agent_id, action_hash, policy_id)
            
            # Return the signed receipt
            return jsonify(receipt.to_dict()), 200
        
        except Exception as e:
            logger.error(f"Error in /prove: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/verify', methods=['POST'])
    def verify():
        """
        Verify an execution receipt signature.
        
        This allows callers to cryptographically verify a receipt
        without needing access to the signer.
        
        Request body: ExecutionReceipt JSON
        """
        try:
            data = request.get_json()
            
            # Reconstruct the receipt from JSON
            receipt = ExecutionReceipt(
                receipt_id=data.get('receipt_id'),
                agent_id=data.get('agent_id'),
                action_hash=data.get('action_hash'),
                policy_id=data.get('policy_id'),
                merkle_root=data.get('merkle_root'),
                timestamp=data.get('timestamp'),
                signature=data.get('signature')
            )
            
            # Verify the signature
            is_valid = signer.verify_receipt(receipt)
            
            return jsonify({
                "receipt_id": receipt.receipt_id,
                "valid": is_valid
            }), 200
        
        except Exception as e:
            logger.error(f"Error in /verify: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/audit-log', methods=['GET'])
    def audit_log():
        """
        Get audit log entries.
        
        ⚠️ In production: This would require authentication and authorization.
        For this MVP, we expose it for transparency.
        """
        entries = signer.audit_log.get_entries()
        root = signer.audit_log.get_root()
        
        return jsonify({
            "merkle_root": root,
            "entry_count": len(entries),
            "entries": entries
        }), 200


class HostAPI:
    """
    REST API server running in the untrusted host environment.
    
    This is the public-facing interface that:
    - Accepts proof requests from agents/orchestrators
    - Forwards to trusted_core via the client bridge
    - Returns signed execution receipts
    
    In production (Nitro Enclave):
    - This would run on the EC2 host
    - Communication would be over vsock to the enclave
    - Would verify attestation documents
    """
    
    def __init__(self, signer: Signer):
        """
        Initialize the host API.
        
        Args:
            signer: Reference to trusted_core signer
        """
        self.signer = signer
        setup_routes(signer)

