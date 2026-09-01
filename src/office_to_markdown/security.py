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
        raise ValidationError("所选文件不存在。")
    if source.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ValidationError("仅支持 DOCX、PPTX 和 XLSX 文件。")
    if source.stat().st_size > MAX_COMPRESSED_BYTES:
        raise ValidationError("所选文件超过配置的大小限制。")
    try:
        with zipfile.ZipFile(source) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ARCHIVE_ENTRIES:
                raise ValidationError("Office 文件包包含过多条目。")
            total_size = sum(item.file_size for item in entries)
            if total_size > MAX_EXPANDED_BYTES:
                raise ValidationError("Office 文件包解压后超过配置的大小限制。")
            names = {item.filename for item in entries}
            if "[Content_Types].xml" not in names:
                raise ValidationError("所选文件不是有效的 OOXML 文件包。")
            if REQUIRED_PARTS[source.suffix.lower()] not in names:
                raise ValidationError("文件内容与其 Office 扩展名不匹配。")
            if any(name.startswith(("/", "\\")) or ".." in Path(name).parts for name in names):
                raise ValidationError("Office 文件包包含不安全的压缩路径。")
            if any(name.lower().endswith("vbaproject.bin") for name in names):
                raise ValidationError("不接受包含宏的文件。")
    except zipfile.BadZipFile as error:
        raise ValidationError("所选文件不是可读取的 OOXML 文件包。") from error


def ensure_output_parent(path: Path) -> None:
    if not path.is_dir():
        raise ValidationError("请选择一个已存在的输出目录。")
