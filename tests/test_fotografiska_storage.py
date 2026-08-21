import pytest

from takeover_fotografiska.storage import encrypted_object_key, encrypted_object_prefix


def test_encrypted_uploads_use_public_bucket_prefix() -> None:
    assert encrypted_object_key("ave", "namespace", "contribution") == (
        "public/ave/namespace/contribution.enc"
    )
    assert encrypted_object_prefix("ave", "namespace") == "public/ave/namespace/"


def test_encrypted_upload_key_rejects_path_injection() -> None:
    with pytest.raises(ValueError):
        encrypted_object_key("../ave", "namespace", "contribution")
