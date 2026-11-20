"""Durable JSON publication without exposing partially written final files."""
from __future__ import annotations

import json
import os
from pathlib import Path
import time


REPLACE_ATTEMPTS = 8
WINDOWS_LOCK_ERRORS = {5, 32, 33}  # access denied / sharing / lock violation


def retry_file_operation(operation):
    """Retry transient Windows locks, then fail; never delete the destination.

    Eight attempts sleep for at most 2.25 seconds in total. Other I/O errors
    propagate immediately. A persistent failure leaves the previous journal
    and the fsynced temporary file available for diagnosis/recovery.
    """
    for attempt in range(REPLACE_ATTEMPTS):
        try:
            return operation()
        except OSError as exc:
            if getattr(exc, "winerror", None) not in WINDOWS_LOCK_ERRORS or attempt == REPLACE_ATTEMPTS - 1:
                raise
            time.sleep(min(0.05 * 2**attempt, 0.5))


def write_temporary(path, value, *, replace_existing):
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w" if replace_existing else "x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    return temporary


def publish_new(temporary, path):
    if os.name == "nt":
        # Windows rename is atomic and refuses an existing destination.
        retry_file_operation(lambda: os.rename(temporary, path))
    else:
        # POSIX rename would overwrite: use an exclusive atomic hard link.
        os.link(temporary, path)
        temporary.unlink()


def save_json_new(path, value):
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing artifact: {path}")
    temporary = write_temporary(path, value, replace_existing=False)
    publish_new(temporary, path)


def replace_json(path, value):
    path = Path(path)
    temporary = write_temporary(path, value, replace_existing=True)
    retry_file_operation(lambda: os.replace(temporary, path))
