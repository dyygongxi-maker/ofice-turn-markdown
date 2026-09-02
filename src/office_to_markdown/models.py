from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path


@dataclass(frozen=True)
class WarningItem:
    code: str
    message: str
    location: str | None = None


@dataclass
class Block:
    kind: str
    text: str = ""
    level: int = 0
    rows: list[list[str]] = field(default_factory=list)
    asset_name: str | None = None


@dataclass
class Asset:
    name: str
    data: bytes


@dataclass
class ParsedDocument:
    title: str
    format: str
    blocks: list[Block] = field(default_factory=list)
    sheets: dict[str, list[Block]] = field(default_factory=dict)
    assets: list[Asset] = field(default_factory=list)
    warnings: list[WarningItem] = field(default_factory=list)


@dataclass(frozen=True)
class ConversionResult:
    output_path: Path
    report_path: Path
    warnings: tuple[WarningItem, ...]


@dataclass(frozen=True)
class ConversionOptions:
    obsidian_mode: bool = False
    tags: tuple[str, ...] = ()
    include_frontmatter: bool = False
    include_source_link: bool = False
    source_link_root: Path | None = None
    copy_source: bool = False
    export_pptx_png: bool = False
    export_pptx_pdf: bool = False


class BatchStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class BatchItem:
    source_path: Path
    status: BatchStatus
    result: ConversionResult | None = None
    error_code: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class BatchResult:
    items: tuple[BatchItem, ...]
    started_at: datetime
    completed_at: datetime

    def count(self, status: BatchStatus) -> int:
        return sum(item.status == status for item in self.items)
