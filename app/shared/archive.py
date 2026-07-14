"""Multi-format archive extraction helper.

Streamlit's file_uploader can only accept one or more file extensions,
but each format needs a different unpacker. This module normalizes that:
pass it the uploaded bytes + filename, get the archive's contents
extracted to a directory.

Supported: .zip, .7z, .tar, .tar.gz, .tgz
"""
from __future__ import annotations
import io
import tarfile
import zipfile
from pathlib import Path


#: Extensions the file_uploader should accept (matches Streamlit's `type=` list).
SUPPORTED_UPLOAD_TYPES: list[str] = ["zip", "7z", "tar", "gz", "tgz"]


def extract_archive(data: bytes, dest: Path, filename: str) -> None:
    """Extract a binary archive blob to ``dest``, auto-dispatched on filename.

    Args:
        data: The raw bytes of the uploaded file (e.g. ``uploaded.read()``).
        dest: Destination directory. Created if missing.
        filename: Original filename (used to pick the format).

    Raises:
        ValueError: If ``filename``'s extension is not one of the supported set.
        RuntimeError: If a .7z file is given but py7zr is not installed.
    """
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)

    name = filename.lower()
    if name.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            zf.extractall(path=str(dest))
        return

    if name.endswith(".7z"):
        try:
            import py7zr  # noqa: WPS433 — lazy import; py7zr is heavy
        except ImportError as e:
            raise RuntimeError(
                "7-Zip archive support requires py7zr. "
                "Install with `pip install py7zr` — or re-pack as .zip."
            ) from e
        _extract_7z_robust(data, dest)
        return

    if name.endswith((".tar", ".tar.gz", ".tgz")):
        # tarfile auto-detects gzip / bzip2 / xz from magic bytes.
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as tf:
            tf.extractall(path=str(dest))
        return

    raise ValueError(
        f"Unsupported archive format: {filename!r}. "
        f"Use one of: .zip, .7z, .tar, .tar.gz, .tgz"
    )


def _extract_7z_robust(data: bytes, dest: Path) -> None:
    """Extract a .7z archive bypassing py7zr's two known bugs:

    1. **Duplicate-mkdir on dir entries**: py7zr 1.1's extractall calls
       os.mkdir without exist_ok for directory entries, raising
       FileExistsError when file entries already auto-created the parent.

    2. **Zero-byte file at directory path**: some archives encode a path
       like ``crRNA_analysis/figures`` as a *file* entry (sometimes the
       is_directory flag is missing), so py7zr writes a 0-byte regular
       file there. Later when ``crRNA_analysis/figures/rmsd.png`` tries to
       open, it hits ENOTDIR because the parent is a file.

    Workaround: scan the entry list, identify entries whose path is a
    PREFIX of another entry's path (those are directories pretending to
    be files), exclude them from the extraction target list, and only
    extract real leaf files. py7zr's makedirs-on-extract handles the
    parent directory creation correctly for real files.
    """
    import io as _io
    import py7zr

    with py7zr.SevenZipFile(_io.BytesIO(data), mode="r") as zf:
        entries = zf.list()

    all_names = [e.filename for e in entries]
    file_targets: list[str] = []
    for entry in entries:
        if entry.is_directory:
            continue
        # If this name is a parent of another entry, it's actually a
        # directory mis-tagged as a file. Skip it; the real children's
        # extraction will create the directory via makedirs.
        prefix = entry.filename + "/"
        is_actually_dir = any(
            other != entry.filename and other.startswith(prefix)
            for other in all_names
        )
        if is_actually_dir:
            continue
        file_targets.append(entry.filename)

    if not file_targets:
        # Empty archive — nothing to do.
        return

    # Re-open for the actual extract. Use the targets list to skip
    # mis-tagged dir entries.
    with py7zr.SevenZipFile(_io.BytesIO(data), mode="r") as zf:
        zf.extract(path=str(dest), targets=file_targets)
