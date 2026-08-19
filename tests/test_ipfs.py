import json
from pathlib import Path

import pytest

from takeover.ipfs import IPFSObject, IPFSUploadError, JSONContributionRegistry, new_contribution, storage_metrics, upload_to_filebase


class Response:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self) -> bytes:
        return json.dumps({"Name": "photo.tif", "Hash": "bafy-test", "Size": "3"}).encode()


def test_filebase_upload_is_authenticated_server_side(monkeypatch) -> None:
    observed = {}

    def fake_urlopen(request, timeout):
        observed["request"] = request
        observed["timeout"] = timeout
        return Response()

    monkeypatch.setattr("takeover.ipfs.urlopen", fake_urlopen)
    obj = upload_to_filebase(filename="photo.tif", content=b"abc", mime_type="image/tiff", token="secret")

    assert obj.cid == "bafy-test"
    assert obj.bytes == 3
    assert observed["request"].get_header("Authorization") == "Bearer secret"
    assert b'name="file"; filename="photo.tif"' in observed["request"].data


def test_upload_requires_nonempty_content_and_cid(monkeypatch) -> None:
    with pytest.raises(ValueError, match="empty"):
        upload_to_filebase(filename="empty", content=b"", mime_type="", token="secret")

    monkeypatch.setattr("takeover.ipfs.urlopen", lambda *_args, **_kwargs: type("NoCid", (), {"__enter__": lambda self: self, "__exit__": lambda self, *_: None, "read": lambda self: b"{}"})())
    with pytest.raises(IPFSUploadError, match="no CID"):
        upload_to_filebase(filename="file", content=b"x", mime_type="", token="secret")


def test_registry_records_provenance_and_metrics_deduplicate_cids(tmp_path: Path) -> None:
    registry = JSONContributionRegistry(tmp_path / "registry.json")
    first = new_contribution("ave", IPFSObject("bafy-one", "a.tif", 10, "image/tiff"))
    registry.add(first)
    second = new_contribution("kumiori", IPFSObject("bafy-one", "a-copy.tif", 10, "image/tiff"))
    registry.add(second)

    rows = registry.list()
    assert rows[0].provenance == {"activation": "application", "source": "takeover_drop"}
    assert rows[0].state == {"pinned": True, "activated": False}
    assert storage_metrics(rows) == {"weight": 10, "objects": 2, "cids": 1}
