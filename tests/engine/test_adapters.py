from datetime import datetime, timezone

from takeover_adapters import DevelopmentJsonContributionRegistry, SessionRegistry, storage_object_from_s3
from takeover_engine import Authority, Contribution, CryptoEnvelope


def test_session_registry_declares_provisional_authority() -> None:
    assert SessionRegistry({}).read().authority is Authority.PROVISIONAL


def test_s3_adapter_and_development_registry_contract(tmp_path) -> None:
    stored = storage_object_from_s3({"Key": "cipher.bin", "Size": 12, "LastModified": datetime.now(timezone.utc)})
    crypto = CryptoEnvelope(1, "AES-256-GCM", "iv", "HKDF-SHA-256", "salt", "wrap", "key", "participant:p:v1")
    row = Contribution("c-1", "p", datetime.now(timezone.utc), stored, crypto)
    registry = DevelopmentJsonContributionRegistry(tmp_path / "registry.json")
    assert registry.add(row) == row
    assert registry.add(row) == row
    assert registry.list() == (row,)
