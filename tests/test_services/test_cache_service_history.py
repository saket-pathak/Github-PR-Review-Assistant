import os
from app.services.cache_service import ReviewCache

def test_reviews_history_insert_and_retrieval(tmp_path):
    db_file = tmp_path / "test_history.db"
    cache = ReviewCache(db_path=str(db_file))

    # Should start empty
    assert cache.get_reviews_history() == []
    assert cache.get_review_by_id(1) is None

    # Log a review run
    cache.add_review_to_history(
        platform="github",
        repo="owner/repo",
        pr_number=42,
        status="success",
        summary="This is a fantastic review summary",
        comments_posted=3
    )

    # Fetch history list
    history = cache.get_reviews_history()
    assert len(history) == 1
    record = history[0]
    assert record["platform"] == "github"
    assert record["repo"] == "owner/repo"
    assert record["pr_number"] == 42
    assert record["status"] == "success"
    assert record["summary"] == "This is a fantastic review summary"
    assert record["comments_posted"] == 3
    assert "created_at" in record

    # Fetch record by id
    by_id = cache.get_review_by_id(record["id"])
    assert by_id is not None
    assert by_id["repo"] == "owner/repo"
    assert by_id["pr_number"] == 42

    # Insert another review run
    cache.add_review_to_history(
        platform="gitlab",
        repo="owner2/repo2",
        pr_number=100,
        status="failure",
        summary="Review failed",
        comments_posted=0
    )

    # Fetch all, newest should be first
    all_history = cache.get_reviews_history()
    assert len(all_history) == 2
    assert all_history[0]["platform"] == "gitlab"
    assert all_history[1]["platform"] == "github"
