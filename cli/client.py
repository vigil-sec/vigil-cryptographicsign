# UNTRUSTED CLI CODE
# HTTP client for communicating with Vigil proof service

import requests
import json
import sys
from typing import Dict, Any, Optional
from urllib.parse import urljoin


class VigilClient:
    """
    HTTP client for the Vigil proof service.
    
    This is an UNTRUSTED component - it makes calls to the service
    but never performs cryptographic operations itself.
    
    All signing and audit operations happen server-side.
    """
    
    def __init__(self, endpoint: str):
        """
        Initialize the client.
        
        Args:
            endpoint: Base URL of Vigil service (e.g., http://localhost:5000)
        """
        self.endpoint = endpoint.rstrip('/')
        self.session = requests.Session()
    
    def prove(self, agent_id: str, action_hash: str, policy_id: str) -> Dict[str, Any]:
        """
        Request a cryptographic proof for an action.
        
        Args:
            agent_id: Agent identifier
            action_hash: Hash of the action (SHA256 format)
            policy_id: Policy identifier
        
        Returns:
            ExecutionReceipt (dict)
        
        Raises:
            requests.RequestException: Network or API error
        """
        url = urljoin(self.endpoint, '/prove')
        payload = {
            'agent_id': agent_id,
            'action_hash': action_hash,
            'policy_id': policy_id
        }
        
        response = self.session.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        return response.json()
    
    def verify(self, receipt: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify an execution receipt signature.
        
        Args:
            receipt: ExecutionReceipt to verify
        
        Returns:
            Dict with 'receipt_id' and 'valid' (bool)
        
        Raises:
            requests.RequestException: Network or API error
        """
        url = urljoin(self.endpoint, '/verify')
        
        response = self.session.post(url, json=receipt, timeout=10)
        response.raise_for_status()
        
        return response.json()
    
    def get_audit_log(self) -> Dict[str, Any]:
        """
        Get the current audit log state.
        
        Args:
            None
        
        Returns:
            Dict with 'merkle_root', 'entry_count', 'entries'
        
        Raises:
            requests.RequestException: Network or API error
        """
        url = urljoin(self.endpoint, '/audit-log')
        
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        
        return response.json()
    
    def is_healthy(self) -> bool:
        """
        Check if the service is healthy (no-op endpoint).
        
        Returns:
            True if service responds, False otherwise
        """
        try:
            url = urljoin(self.endpoint, '/health')
            response = self.session.get(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
