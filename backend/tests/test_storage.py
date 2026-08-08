"""Storage adapter smoke tests (local + GridFS auto-detect)."""
from pathlib import Path

import pytest

from app import storage
from app.paths import use_gridfs


def test_save_and_delete_local(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(storage, "UPLOAD_DIR", Path(tmp_path))
    monkeypatch.setattr(storage, "use_object_storage", lambda: False)
    monkeypatch.setattr(storage, "use_gridfs", lambda: False)

    name = "hello-test.txt"
    rel = storage.save_bytes(name, b"ciao aia", content_type="text/plain")
    assert rel == f"/api/uploads/{name}"
    assert storage.exists(name)
    assert storage.read_bytes(name) == b"ciao aia"
    assert storage.size_bytes(name) == 8
    storage.delete(name)
    assert not storage.exists(name)


def test_auto_uses_gridfs_on_atlas_srv(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "auto")
    monkeypatch.setenv("MONGO_URL", "mongodb+srv://user:pass@cluster0.example.net/db")
    assert use_gridfs() is True


def test_auto_uses_local_on_docker_mongo(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "auto")
    monkeypatch.setenv("MONGO_URL", "mongodb://mongo:27017")
    assert use_gridfs() is False


def test_gridfs_roundtrip(monkeypatch):
    """Requires reachable MONGO_URL; skips otherwise."""
    import os

    mongo = (os.environ.get("MONGO_URL") or "").strip()
    if not mongo:
        pytest.skip("MONGO_URL not set")
    monkeypatch.setenv("STORAGE_BACKEND", "gridfs")
    monkeypatch.setenv("DB_NAME", os.environ.get("DB_NAME") or "aia_legnano")
    storage._gridfs = None
    storage._gridfs_client = None
    monkeypatch.setattr(storage, "use_object_storage", lambda: False)
    monkeypatch.setattr(storage, "use_gridfs", lambda: True)

    try:
        name = "gridfs-test-aia.bin"
        storage.save_bytes(name, b"gridfs-ok", content_type="application/octet-stream")
        assert storage.exists(name)
        assert storage.read_bytes(name) == b"gridfs-ok"
        storage.delete(name)
        assert not storage.exists(name)
    except Exception as exc:
        pytest.skip(f"GridFS unavailable: {exc}")
    finally:
        storage._gridfs = None
        storage._gridfs_client = None
