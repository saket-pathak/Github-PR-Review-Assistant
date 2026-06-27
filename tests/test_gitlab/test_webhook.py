from app.gitlab.webhook import verify_gitlab_token, parse_gitlab_webhook

def test_verify_gitlab_token_no_secret():
    assert verify_gitlab_token("token", "") is True

def test_verify_gitlab_token_missing_token():
    assert verify_gitlab_token("", "secret") is False

def test_verify_gitlab_token_valid():
    assert verify_gitlab_token("my-secret-token", "my-secret-token") is True

def test_verify_gitlab_token_invalid():
    assert verify_gitlab_token("wrong-token", "my-secret-token") is False

def test_parse_gitlab_webhook_wrong_event():
    assert parse_gitlab_webhook({}, "Push Hook") is None

def test_parse_gitlab_webhook_wrong_action():
    payload = {
        "object_attributes": {
            "action": "close",
            "iid": 10
        },
        "project": {
            "path_with_namespace": "gitlab-org/gitlab"
        }
    }
    assert parse_gitlab_webhook(payload, "Merge Request Hook") is None

def test_parse_gitlab_webhook_missing_mr_or_project():
    payload_no_mr = {
        "object_attributes": {
            "action": "open"
        },
        "project": {
            "path_with_namespace": "gitlab-org/gitlab"
        }
    }
    assert parse_gitlab_webhook(payload_no_mr, "Merge Request Hook") is None
    
    payload_no_project = {
        "object_attributes": {
            "action": "open",
            "iid": 10
        }
    }
    assert parse_gitlab_webhook(payload_no_project, "Merge Request Hook") is None

def test_parse_gitlab_webhook_valid_with_namespace():
    payload = {
        "object_attributes": {
            "action": "open",
            "iid": 42
        },
        "project": {
            "path_with_namespace": "gitlab-org/gitlab-test"
        }
    }
    result = parse_gitlab_webhook(payload, "Merge Request Hook")
    assert result == ("gitlab-org/gitlab-test", 42)

def test_parse_gitlab_webhook_fallback_to_id():
    payload = {
        "object_attributes": {
            "action": "update",
            "iid": 101
        },
        "project": {
            "id": 9876
        }
    }
    result = parse_gitlab_webhook(payload, "Merge Request Hook")
    assert result == ("9876", 101)
