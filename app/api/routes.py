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
    Manually trigger a review for a PR.
    """
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
async def github_webhook(
    request: Request, 
    background_tasks: BackgroundTasks, 
    x_hub_signature_256: str = Header(None)
):
    """
    GitHub webhook receiver.
    """
    payload_bytes = await request.body()
    
    # Verify webhook signature using secret
    if settings.github_webhook_secret:
        try:
            from app.github.webhook import verify_signature
            if not verify_signature(payload_bytes, x_hub_signature_256, settings.github_webhook_secret):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
        except (ImportError, AttributeError):
            # Fallback if webhook signature check is not yet implemented
            pass
            
    payload = await request.json()
    event = request.headers.get("X-GitHub-Event", "")
    
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
        return {"status": "triggered", "repo": repo, "pr": pr_number}
    except (ImportError, AttributeError):
        return {"status": "received", "repo": repo, "pr": pr_number, "note": "Review service not yet implemented"}
