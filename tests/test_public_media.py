from takeover.public_media import FilebasePublicMediaStore


class FakeS3:
    def __init__(self):
        self.put = None

    def put_object(self, **kwargs):
        self.put = kwargs

    def head_object(self, **_kwargs):
        return {"Metadata": {"cid": "bafy-avatar"}}


def test_avatar_upload_returns_durable_gateway_url_and_stable_object_key() -> None:
    client = FakeS3()
    store = FilebasePublicMediaStore(
        client, "takeover-fotografiska", "https://gateway.example/ipfs/",
    )

    uploaded = store.save_avatar(
        player_id="player_123",
        filename="My portrait.jpg",
        content_type="image/jpeg",
        data=b"image-bytes",
    )

    assert uploaded.url == "https://gateway.example/ipfs/bafy-avatar"
    assert uploaded.object_key.startswith("public/avatars/player_123/")
    assert uploaded.object_key.endswith("-My-portrait.jpg")
    assert client.put["ContentType"] == "image/jpeg"
    assert client.put["Body"] == b"image-bytes"
