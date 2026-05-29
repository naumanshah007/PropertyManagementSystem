"""Storage root resolution + crash-safe writes.

`STORAGE_ROOT` is the on-disk root for the JSON/local backend. It honours the
`DATA_DIR` env var so the backend host can point it at a mounted persistent
disk (otherwise data is lost on every redeploy). `atomic_write_text` writes via
a temp file + `os.replace` so a crash mid-write can never leave a half-written,
unparseable JSON file behind.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

_DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "storage" / "organisations"


def _resolve_root() -> Path:
    data_dir = os.getenv("DATA_DIR")
    if data_dir and data_dir.strip():
        return Path(data_dir.strip()) / "organisations"
    return _DEFAULT_ROOT


STORAGE_ROOT = _resolve_root()


def atomic_write_text(path: Path | str, text: str, *, encoding: str = "utf-8") -> None:
    """Atomically write text to ``path`` (temp file in the same dir + os.replace)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=path.suffix)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
