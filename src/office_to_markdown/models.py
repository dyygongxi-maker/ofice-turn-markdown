from __future__ import annotations

from dataclasses import dataclass, field
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
