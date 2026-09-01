from __future__ import annotations

import re
import zipfile
from pathlib import Path


class ValidationError(ValueError):
    pass


ALLOWED_SUFFIXES = {".docx", ".pptx", ".xlsx"}
REQUIRED_PARTS = {
    ".docx": "word/document.xml",
    ".pptx": "ppt/presentation.xml",
    ".xlsx": "xl/workbook.xml",
}
MAX_COMPRESSED_BYTES = 100 * 1024 * 1024
MAX_EXPANDED_BYTES = 300 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 10_000


def safe_name(value: str, fallback: str = "document") -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip(".-")
    return normalized[:80] or fallback


def validate_input(source: Path) -> None:
    if not source.is_file():
        raise ValidationError("The selected file does not exist.")
    if source.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ValidationError("Only DOCX, PPTX, and XLSX files are supported.")
    if source.stat().st_size > MAX_COMPRESSED_BYTES:
        raise ValidationError("The selected file exceeds the configured size limit.")
    try:
        with zipfile.ZipFile(source) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ARCHIVE_ENTRIES:
                raise ValidationError("The Office package contains too many entries.")
            total_size = sum(item.file_size for item in entries)
            if total_size > MAX_EXPANDED_BYTES:
                raise ValidationError("The Office package expands beyond the configured limit.")
            names = {item.filename for item in entries}
            if "[Content_Types].xml" not in names:
                raise ValidationError("The selected file is not a valid OOXML package.")
            if REQUIRED_PARTS[source.suffix.lower()] not in names:
                raise ValidationError("The file content does not match its Office extension.")
            if any(name.startswith(("/", "\\")) or ".." in Path(name).parts for name in names):
                raise ValidationError("The Office package contains an unsafe archive path.")
            if any(name.lower().endswith("vbaproject.bin") for name in names):
                raise ValidationError("Macro-enabled content is not accepted.")
    except zipfile.BadZipFile as error:
        raise ValidationError("The selected file is not a readable OOXML package.") from error


def ensure_output_parent(path: Path) -> None:
    if not path.is_dir():
        raise ValidationError("Choose an existing output folder.")
