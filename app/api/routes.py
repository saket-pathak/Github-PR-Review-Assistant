from fastapi import APIRouter, Header, HTTPException, Request
from app.api.schemas import ReviewRequest, ReviewResponse

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
    # Mock review response based on README specifications
    return ReviewResponse(
        status="success",
        pr=payload.pr_number,
        comments_posted=5,
        summary=f"The PR introduces changes in {payload.repo}. (Mock summary: Key concerns: none)"
    )

@router.post("/webhook")
async def github_webhook(request: Request, x_hub_signature_256: str = Header(None)):
    """
    GitHub webhook receiver.
    """
    # Stub implementation for webhook receipt
    payload = await request.json()
    return {"status": "received", "event": request.headers.get("X-GitHub-Event")}
