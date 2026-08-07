"""Shared filesystem paths for the backend."""

import os
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", str(BACKEND_ROOT / "uploads")))
