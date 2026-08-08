"""Local storage adapter smoke tests (no S3 credentials required)."""
from pathlib import Path

from app import storage
from app.paths import UPLOAD_DIR


def test_save_and_delete_local(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    # Re-bind module paths used by storage
    monkeypatch.setattr(storage, "UPLOAD_DIR", Path(tmp_path))
    monkeypatch.setattr(storage, "use_object_storage", lambda: False)

    name = "hello-test.txt"
    rel = storage.save_bytes(name, b"ciao aia", content_type="text/plain")
    assert rel == f"/api/uploads/{name}"
    assert storage.exists(name)
    assert storage.read_bytes(name) == b"ciao aia"
    assert storage.size_bytes(name) == 8
    storage.delete(name)
    assert not storage.exists(name)
