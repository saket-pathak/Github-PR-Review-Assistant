import hmac
import hashlib
from typing import Dict, Any, Optional

def verify_bitbucket_signature(
    payload_bytes: bytes,
    signature_header: Optional[str],
    secret: str
) -> bool:
    """
    Verifies the signature of the Bitbucket webhook request.
    Bitbucket sends 'X-Hub-Signature' as 'sha256=<hmac>' when a secret is configured.
    """
    if not secret:
        return True
        
    if not signature_header:
        return False
        
    try:
        algo, signature = signature_header.split('=', 1)
    except ValueError:
        return False
        
    if algo.lower() != 'sha256':
        return False
        
    expected_signature = hmac.new(
        key=secret.encode('utf-8'),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)

def parse_bitbucket_webhook(
    payload: Dict[str, Any],
    event: str
) -> Optional[tuple[str, int]]:
    """
    Parses the webhook payload from Bitbucket Cloud pull request events.
    Listens for 'pullrequest:created' and 'pullrequest:updated'.
    Returns (repo_full_name, pr_id) if eligible, otherwise None.
    """
    if event not in ("pullrequest:created", "pullrequest:updated"):
        return None
        
    pr = payload.get("pullrequest", {})
    pr_id = pr.get("id")
    repo = pr.get("destination", {}).get("repository", {}).get("full_name")
    
    if not pr_id or not repo:
        return None
        
    return repo, int(pr_id)
