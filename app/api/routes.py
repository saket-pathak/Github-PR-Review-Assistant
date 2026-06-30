from fastapi import APIRouter, Header, HTTPException, Request, BackgroundTasks
from app.api.schemas import ReviewRequest, ReviewResponse
from app.config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}

@router.post("/review", response_model=ReviewResponse)
async def review_pr(payload: ReviewRequest):
    """
    Manually trigger a review for a PR (GitHub) or MR (GitLab).
    """
    if payload.platform == "gitlab":
        try:
            from app.services.gitlab_review_service import run_gitlab_review
            result = await run_gitlab_review(payload.repo, payload.pr_number, post_to_gitlab=True)
            return ReviewResponse(
                status=result.get("status", "success"),
                pr=payload.pr_number,
                comments_posted=result.get("comments_posted", 0),
                summary=result.get("summary", "")
            )
        except (ImportError, AttributeError) as e:
            return ReviewResponse(
                status="mocked",
                pr=payload.pr_number,
                comments_posted=0,
                summary=f"GitLab Review service error or not implemented: {e}"
            )
    else:
        try:
            from app.services.review_service import run_review
            result = await run_review(payload.repo, payload.pr_number, post_to_github=True)
            return ReviewResponse(
                status=result.get("status", "success"),
                pr=payload.pr_number,
                comments_posted=result.get("comments_posted", 0),
                summary=result.get("summary", "")
            )
        except (ImportError, AttributeError):
            return ReviewResponse(
                status="mocked",
                pr=payload.pr_number,
                comments_posted=0,
                summary="Review service not implemented yet."
            )

@router.post("/webhook")
async def webhook(
    request: Request, 
    background_tasks: BackgroundTasks, 
    x_hub_signature_256: str = Header(None),
    x_github_event: str = Header(None, alias="X-GitHub-Event"),
    x_gitlab_event: str = Header(None, alias="X-Gitlab-Event"),
    x_gitlab_token: str = Header(None, alias="X-Gitlab-Token")
):
    """
    Unified webhook receiver for GitHub and GitLab.
    """
    payload_bytes = await request.body()
    
    # 1. Process GitLab webhook if X-Gitlab-Event is present
    if x_gitlab_event:
        if settings.gitlab_webhook_secret:
            from app.gitlab.webhook import verify_gitlab_token
            if not verify_gitlab_token(x_gitlab_token, settings.gitlab_webhook_secret):
                raise HTTPException(status_code=401, detail="Invalid GitLab webhook token")
                
        payload = await request.json()
        from app.gitlab.webhook import parse_gitlab_webhook
        extracted = parse_gitlab_webhook(payload, x_gitlab_event)
        
        if not extracted:
            return {"status": "ignored", "reason": "Not an eligible merge request event or webhook parser not ready"}
            
        project_path, mr_iid = extracted
        
        from app.services.gitlab_review_service import run_gitlab_review
        background_tasks.add_task(run_gitlab_review, project_path, mr_iid, post_to_gitlab=True)
        return {"status": "triggered", "platform": "gitlab", "repo": project_path, "pr": mr_iid}

    # 2. Otherwise process as GitHub webhook
    if settings.github_webhook_secret:
        try:
            from app.github.webhook import verify_signature
            if not verify_signature(payload_bytes, x_hub_signature_256, settings.github_webhook_secret):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
        except (ImportError, AttributeError):
            pass
            
    payload = await request.json()
    event = x_github_event or ""
    
    try:
        from app.github.webhook import parse_webhook_payload
        extracted = parse_webhook_payload(payload, event)
    except (ImportError, AttributeError):
        extracted = None
        
    if not extracted:
        return {"status": "ignored", "reason": "Not an eligible pull_request event or webhook parser not ready"}
        
    repo, pr_number = extracted
    
    try:
        from app.services.review_service import run_review
        background_tasks.add_task(run_review, repo, pr_number, post_to_github=True)
        return {"status": "triggered", "platform": "github", "repo": repo, "pr": pr_number}
    except (ImportError, AttributeError):
        return {"status": "received", "repo": repo, "pr": pr_number, "note": "Review service not yet implemented"}
