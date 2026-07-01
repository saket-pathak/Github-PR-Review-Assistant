import pytest
from app.bitbucket.webhook import verify_bitbucket_signature, parse_bitbucket_webhook

def test_verify_bitbucket_signature_no_secret():
    assert verify_bitbucket_signature(b"payload", "sha256=sig", "") is True

def test_verify_bitbucket_signature_missing_header():
    assert verify_bitbucket_signature(b"payload", None, "secret") is False

def test_verify_bitbucket_signature_invalid_format():
    assert verify_bitbucket_signature(b"payload", "invalidsig", "secret") is False

def test_verify_bitbucket_signature_valid():
    import hmac
    import hashlib
    payload = b"test-payload"
    secret = "my-secret"
    sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    assert verify_bitbucket_signature(payload, f"sha256={sig}", secret) is True

def test_verify_bitbucket_signature_invalid():
    assert verify_bitbucket_signature(b"payload", "sha256=wrong", "secret") is False

def test_parse_bitbucket_webhook_wrong_event():
    assert parse_bitbucket_webhook({}, "repo:push") is None

def test_parse_bitbucket_webhook_missing_fields():
    assert parse_bitbucket_webhook({"pullrequest": {}}, "pullrequest:created") is None

def test_parse_bitbucket_webhook_valid():
    payload = {
        "pullrequest": {
            "id": 42,
            "destination": {
                "repository": {
                    "full_name": "workspace/repo"
                }
            }
        }
    }
    res = parse_bitbucket_webhook(payload, "pullrequest:created")
    assert res == ("workspace/repo", 42)
    
    res2 = parse_bitbucket_webhook(payload, "pullrequest:updated")
    assert res2 == ("workspace/repo", 42)
