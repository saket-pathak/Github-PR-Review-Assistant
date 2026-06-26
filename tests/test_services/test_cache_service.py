from app.services.cache_service import ReviewCache

def test_cache_set_and_get(tmp_path):
    db_file = tmp_path / "test_cache.db"
    cache = ReviewCache(db_path=str(db_file))
    
    # Check non-existent entry
    assert cache.get_comments("nonexistent") is None
    
    # Save comments
    comments = [{"path": "a.py", "line": 10, "comment": "good code"}]
    cache.set_comments("hash123", comments)
    
    # Retrieve comments
    retrieved = cache.get_comments("hash123")
    assert retrieved == comments
    
    # Overwrite comments
    new_comments = []
    cache.set_comments("hash123", new_comments)
    assert cache.get_comments("hash123") == []

