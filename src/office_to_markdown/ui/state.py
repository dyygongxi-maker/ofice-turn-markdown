from __future__ import annotations

import tkinter as tk
from enum import StrEnum
from pathlib import Path

from ..models import BatchItem, BatchResult, ConversionOptions
from ..security import ValidationError, validate_tags


class UiPhase(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    CANCELLING = "cancelling"
    COMPLETED = "completed"


class UiState:
    """Single UI-owned state boundary; conversion work remains outside this class."""

    def __init__(self, master: tk.Misc, default_output: Path | None = None) -> None:
        self.output = tk.StringVar(master, str(default_output) if default_output else "")
        self.tags = tk.StringVar(master)
        self.vault_root = tk.StringVar(master)
        self.status = tk.StringVar(master, "尚未添加文件，文件仅在本机处理。")
        self.recursive = tk.BooleanVar(master, False)
        self.obsidian = tk.BooleanVar(master, False)
        self.include_source_link = tk.BooleanVar(master, False)
        self.copy_source = tk.BooleanVar(master, False)
        self.export_pptx_png = tk.BooleanVar(master, False)
        self.export_pptx_pdf = tk.BooleanVar(master, False)
        self.sources: list[Path] = []
        self.results: dict[str, BatchItem] = {}
        self.selected_key: str | None = None
        self.phase = UiPhase.IDLE

    @property
    def can_edit(self) -> bool:
        return self.phase in {UiPhase.IDLE, UiPhase.COMPLETED}

    @property
    def can_cancel(self) -> bool:
        return self.phase is UiPhase.RUNNING

    @property
    def can_start(self) -> bool:
        return self.can_edit and bool(self.sources) and Path(self.output.get()).is_dir()

    @property
    def selected_item(self) -> BatchItem | None:
        return self.results.get(self.selected_key) if self.selected_key else None

    def set_phase(self, phase: UiPhase) -> None:
        self.phase = phase

    def add_sources(self, paths: tuple[Path, ...] | list[Path]) -> None:
        known = set(self.sources)
        for path in paths:
            if path not in known:
                self.sources.append(path)
                known.add(path)

    def select(self, source: Path | None) -> None:
        self.selected_key = str(source) if source else None

    def apply_item(self, item: BatchItem) -> None:
        self.results[str(item.source_path)] = item

    def apply_result(self, result: BatchResult) -> None:
        for item in result.items:
            self.apply_item(item)

    def build_options(self) -> ConversionOptions:
        tags = tuple(tag.strip() for tag in self.tags.get().split(",") if tag.strip())
        if self.obsidian.get() and not tags:
            tags = ("office-import",)
        validate_tags(tags)
        root = Path(self.vault_root.get()) if self.vault_root.get() else None
        if self.include_source_link.get() and root is None:
            raise ValidationError("添加原文件链接时请先选择 Vault 根目录。")
        if self.copy_source.get() and not self.obsidian.get():
            raise ValidationError("复制原文件仅可在 Obsidian 模式中启用。")
        return ConversionOptions(
            obsidian_mode=self.obsidian.get(),
            include_frontmatter=self.obsidian.get(),
            tags=tags,
            include_source_link=self.include_source_link.get(),
            source_link_root=root,
            copy_source=self.copy_source.get(),
            export_pptx_png=self.export_pptx_png.get(),
            export_pptx_pdf=self.export_pptx_pdf.get(),
        )
