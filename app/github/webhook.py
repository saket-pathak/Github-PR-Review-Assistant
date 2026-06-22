import hmac
import hashlib
from typing import Dict, Any, Tuple, Optional

def verify_signature(payload: bytes, signature_header: str, secret: str) -> bool:
    """
    Verify that the webhook signature matches the payload.
    Uses HMAC SHA-256.
    """
    if not secret:
        return True
        
    if not signature_header:
        return False
        
    if not signature_header.startswith("sha256="):
        return False
        
    signature = signature_header.replace("sha256=", "")
    mac = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256)
    
    return hmac.compare_digest(mac.hexdigest(), signature)


def parse_webhook_payload(payload: Dict[str, Any], event_header: str) -> Optional[Tuple[str, int]]:
    """
    Parses the webhook payload to extract repository full name and PR number.
    Triggers on 'opened', 'synchronize', and 'reopened' pull requests.
    """
    if event_header != "pull_request":
        return None
        
    action = payload.get("action")
    if action not in ["opened", "synchronize", "reopened"]:
        return None
        
    pr_data = payload.get("pull_request")
    repo_data = payload.get("repository")
    
    if not pr_data or not repo_data:
        return None
        
    pr_number = pr_data.get("number")
    repo_full_name = repo_data.get("full_name")
    
    if not pr_number or not repo_full_name:
        return None
        
    return repo_full_name, pr_number
