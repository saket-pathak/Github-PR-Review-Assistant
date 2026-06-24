import hmac
import hashlib
from app.github.webhook import verify_signature, parse_webhook_payload

def test_verify_signature_no_secret():
    # If no secret is configured, validation should always pass/be skipped (returns True)
    assert verify_signature(b"payload", "sha256=sig", "") is True

def test_verify_signature_missing_header():
    assert verify_signature(b"payload", "", "secret") is False

def test_verify_signature_invalid_header_format():
    assert verify_signature(b"payload", "invalidsigformat", "secret") is False

def test_verify_signature_valid():
    secret = "my_secret"
    payload = b"{\"event\": \"test\"}"
    mac = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256)
    expected_signature = f"sha256={mac.hexdigest()}"
    
    assert verify_signature(payload, expected_signature, secret) is True

def test_verify_signature_invalid():
    secret = "my_secret"
    payload = b"{\"event\": \"test\"}"
    wrong_signature = "sha256=1234567890abcdef"
    
    assert verify_signature(payload, wrong_signature, secret) is False


def test_parse_webhook_payload_wrong_event():
    assert parse_webhook_payload({}, "push") is None

def test_parse_webhook_payload_wrong_action():
    payload = {
        "action": "closed",
        "pull_request": {"number": 10},
        "repository": {"full_name": "owner/repo"}
    }
    assert parse_webhook_payload(payload, "pull_request") is None

def test_parse_webhook_payload_missing_pr_or_repo():
    payload_no_pr = {
        "action": "opened",
        "repository": {"full_name": "owner/repo"}
    }
    assert parse_webhook_payload(payload_no_pr, "pull_request") is None
    
    payload_no_repo = {
        "action": "opened",
        "pull_request": {"number": 10}
    }
    assert parse_webhook_payload(payload_no_repo, "pull_request") is None

def test_parse_webhook_payload_valid():
    payload = {
        "action": "synchronize",
        "pull_request": {"number": 42},
        "repository": {"full_name": "owner/repo-name"}
    }
    result = parse_webhook_payload(payload, "pull_request")
    
    assert result == ("owner/repo-name", 42)
