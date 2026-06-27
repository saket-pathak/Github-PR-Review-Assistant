import hmac
from typing import Dict, Any, Tuple, Optional

def verify_gitlab_token(request_token: str, secret: str) -> bool:
    """
    Verify that the GitLab webhook secret token matches the configured secret.
    Uses hmac.compare_digest for constant-time comparison.
    """
    if not secret:
        return True
        
    if not request_token:
        return False
        
    return hmac.compare_digest(request_token.encode("utf-8"), secret.encode("utf-8"))


def parse_gitlab_webhook(payload: Dict[str, Any], event_header: str) -> Optional[Tuple[str, int]]:
    """
    Parses the GitLab webhook payload to extract project namespace/path and MR iid.
    Triggers on merge request events: 'open', 'update', 'reopen' (and variations).
    """
    if event_header != "Merge Request Hook":
        return None
        
    obj_attrs = payload.get("object_attributes") or {}
    action = obj_attrs.get("action")
    
    if action not in ["open", "opened", "update", "reopen", "reopened"]:
        return None
        
    mr_iid = obj_attrs.get("iid")
    
    project = payload.get("project") or {}
    project_path = project.get("path_with_namespace")
    
    # Fallback to project ID as string if path is missing
    if not project_path and "id" in project:
        project_path = str(project["id"])
        
    if not mr_iid or not project_path:
        return None
        
    return project_path, mr_iid
