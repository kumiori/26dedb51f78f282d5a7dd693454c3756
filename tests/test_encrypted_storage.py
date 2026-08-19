from takeover.encrypted_storage import EncryptedContribution, EncryptedRegistry


def test_encrypted_registry_is_private_and_idempotent(tmp_path) -> None:
    registry = EncryptedRegistry(tmp_path / "encrypted.json")
    row = EncryptedContribution(
        id="one",
        contributor_id="ave",
        created_at="2026-08-19T00:00:00+00:00",
        object={"key": "private/ave/object.enc", "cid": "bafy", "encrypted_bytes": 32, "original_bytes": 16},
        crypto={"algorithm": "AES-256-GCM", "version": 1, "wrapped_key": "wrapped"},
    )
    registry.add(row)
    registry.add(row)

    assert registry.list() == [row]
    assert registry.list()[0].visibility == "private"
