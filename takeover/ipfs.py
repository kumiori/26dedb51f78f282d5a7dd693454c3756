"""Small Filebase IPFS upload adapter and Storage v0 contribution registry."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import mimetypes
from pathlib import Path
import secrets
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4


FILEBASE_ADD_URL = "https://rpc.filebase.io/api/v0/add?cid-version=1"


class IPFSUploadError(RuntimeError):
    """Raised when the storage provider does not accept an upload."""


@dataclass(frozen=True)
class IPFSObject:
    cid: str
    filename: str
    bytes: int
    mime_type: str


@dataclass(frozen=True)
class Contribution:
    id: str
    node_id: str
    created_at: str
    object: dict[str, Any]
    provenance: dict[str, str]
    state: dict[str, bool]


def _multipart(filename: str, content: bytes, mime_type: str) -> tuple[bytes, str]:
    boundary = f"takeover-{secrets.token_hex(16)}"
    safe_name = Path(filename).name.replace('"', "") or "contribution.bin"
    body = b"".join(
        (
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="file"; filename="{safe_name}"\r\n'.encode(),
            f"Content-Type: {mime_type}\r\n\r\n".encode(),
            content,
            f"\r\n--{boundary}--\r\n".encode(),
        )
    )
    return body, boundary


def upload_to_filebase(
    *, filename: str, content: bytes, mime_type: str, token: str, timeout: int = 60
) -> IPFSObject:
    """Upload and pin one file through Filebase's authenticated IPFS RPC API."""
    if not token.strip():
        raise ValueError("A Filebase IPFS token is required.")
    if not content:
        raise ValueError("The contribution is empty.")
    resolved_mime = mime_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    body, boundary = _multipart(filename, content, resolved_mime)
    request = Request(
        FILEBASE_ADD_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token.strip()}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise IPFSUploadError(f"Filebase rejected the upload ({exc.code}): {detail}") from exc
    except (URLError, TimeoutError) as exc:
        raise IPFSUploadError(f"Filebase could not be reached: {exc}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IPFSUploadError("Filebase returned an unreadable upload response.") from exc

    cid = str(payload.get("Hash") or payload.get("Cid") or payload.get("cid") or "").strip()
    if not cid:
        raise IPFSUploadError("Filebase accepted the request but returned no CID.")
    return IPFSObject(cid=cid, filename=Path(filename).name, bytes=len(content), mime_type=resolved_mime)


class JSONContributionRegistry:
    """Tiny append-style JSON registry for the isolated Storage v0 experiment."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def list(self) -> list[Contribution]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [Contribution(**item) for item in payload.get("contributions", [])]

    def add(self, contribution: Contribution) -> Contribution:
        rows = self.list()
        if any(row.id == contribution.id for row in rows):
            raise ValueError(f"Contribution id already exists: {contribution.id}")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary.write_text(
            json.dumps({"schema": "takeover-storage/v0", "contributions": [asdict(row) for row in (*rows, contribution)]}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)
        return contribution


def new_contribution(node_id: str, obj: IPFSObject) -> Contribution:
    return Contribution(
        id=str(uuid4()),
        node_id=node_id.strip(),
        created_at=datetime.now(timezone.utc).isoformat(),
        object=asdict(obj),
        provenance={"activation": "application", "source": "takeover_drop"},
        state={"pinned": True, "activated": False},
    )


def storage_metrics(rows: list[Contribution]) -> dict[str, int]:
    unique = {str(row.object["cid"]): int(row.object["bytes"]) for row in rows}
    return {"weight": sum(unique.values()), "objects": len(rows), "cids": len(unique)}
