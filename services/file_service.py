"""
Nexus AI – File Service
========================
Validates, saves, and manages uploaded files.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

# Allowed extensions (kept in sync with config, but also enforced here)
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "pdf", "txt"}


def allowed_file(filename: str) -> bool:
    """Return True if the file extension is permitted."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def save_file(file: FileStorage, upload_folder: str) -> dict[str, Any]:
    """
    Validate and persist an uploaded file.

    Args:
        file: Werkzeug FileStorage object from the request.
        upload_folder: Absolute path to the uploads directory.

    Returns:
        dict with ``file_name``, ``file_path``, ``file_type``.

    Raises:
        ValueError: if the file type is not allowed.
    """
    if not file or not file.filename:
        raise ValueError("No file provided.")

    if not allowed_file(file.filename):
        raise ValueError(
            f"File type not allowed. Accepted types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    original = secure_filename(file.filename)
    ext = original.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}_{original}"

    os.makedirs(upload_folder, exist_ok=True)
    dest = os.path.join(upload_folder, unique_name)
    file.save(dest)

    return {
        "file_name": original,
        "file_path": dest,
        "file_type": ext,
    }
