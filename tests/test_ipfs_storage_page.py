from streamlit.testing.v1 import AppTest
from datetime import datetime, timezone


class FakeS3:
    def list_buckets(self):
        return {"Buckets": [{"Name": "takeover-test"}]}

    def list_objects_v2(self, *, Bucket):
        assert Bucket == "takeover-fotografiska"
        return {"Contents": [{"Key": "existing", "Size": 1024, "LastModified": datetime.now(timezone.utc)}]}

    def put_bucket_cors(self, **_kwargs):
        return {}


def test_storage_page_lists_bucket_accounting(monkeypatch) -> None:
    monkeypatch.setattr("boto3.client", lambda *_args, **_kwargs: FakeS3())
    app = AppTest.from_file("pages/98_IPFS_Storage_Test.py").run(timeout=20)

    assert not app.exception
    assert [title.value for title in app.title] == ["DROP / TEST"]
    assert {metric.label for metric in app.metric} == {"OBJECTS", "BUCKET WEIGHT"}
    assert next(metric.value for metric in app.metric if metric.label == "OBJECTS") == "1"
    assert not app.text_input
    assert not app.get("file_uploader")
    assert any("OPEN A PARTICIPANT DROP LINK" in item.value for item in app.info)
    assert len(app.get("plotly_chart")) == 1
    assert any("TWO-MONTH DISPLAY HORIZON" in item.value for item in app.caption)
