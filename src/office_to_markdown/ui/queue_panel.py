from __future__ import annotations

# ruff: noqa: E501
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import ttk

from ..models import BatchStatus
from .state import UiState

STATUS_TEXT = {
    BatchStatus.PENDING: "等待",
    BatchStatus.RUNNING: "转换中",
    BatchStatus.SUCCESS: "完成",
    BatchStatus.WARNING: "警告",
    BatchStatus.FAILED: "失败",
    BatchStatus.SKIPPED: "跳过",
    BatchStatus.CANCELLED: "已取消",
}

TYPE_TEXT = {
    ".docx": "Word",
    ".pptx": "PowerPoint",
    ".xlsx": "Excel",
    ".pdf": "PDF",
    ".txt": "文本",
}


class QueuePanel(ttk.Frame):
    """Ordered file queue view. Tree ordering never changes state.sources ordering."""

    def __init__(
        self,
        master: tk.Misc,
        state: UiState,
        choose_files: Callable[[], None],
        choose_folder: Callable[[], None],
        open_output: Callable[[], None],
        open_report: Callable[[], None],
    ) -> None:
        super().__init__(master, style="Panel.TFrame", padding=16)
        self.state = state
        self._open_output = open_output
        self._open_report = open_report
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        header = ttk.Frame(self, style="Panel.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="文件队列", style="Heading.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Button(header, text="添加文件", command=choose_files, style="Secondary.TButton").grid(
            row=0, column=1, padx=(8, 0)
        )
        ttk.Button(
            header, text="扫描文件夹", command=choose_folder, style="Secondary.TButton"
        ).grid(row=0, column=2, padx=(8, 0))
        self.recursive = ttk.Checkbutton(self, text="包含子文件夹", variable=state.recursive)
        self.recursive.grid(row=1, column=0, sticky="w", pady=(10, 8))

        holder = ttk.Frame(self, style="Panel.TFrame")
        holder.grid(row=2, column=0, sticky="nsew")
        holder.columnconfigure(0, weight=1)
        holder.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(
            holder,
            columns=("file", "type", "size", "status"),
            selectmode="browse",
            show="headings",
        )
        self.tree.heading("file", text="文件")
        self.tree.heading("type", text="类型")
        self.tree.heading("size", text="大小")
        self.tree.heading("status", text="状态")
        self.tree.column("file", minwidth=220, width=360, stretch=True)
        self.tree.column("type", width=100, minwidth=90, stretch=False)
        self.tree.column("size", width=90, minwidth=80, stretch=False)
        self.tree.column("status", width=90, minwidth=80, stretch=False)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(holder, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        for tag, color in (
            ("success", "#098C28"),
            ("warning", "#B95C00"),
            ("failed", "#C92D2D"),
            ("running", "#3660F4"),
            ("muted", "#808080"),
        ):
            self.tree.tag_configure(tag, foreground=color)

        footer = ttk.Frame(self, style="Panel.TFrame")
        footer.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        footer.columnconfigure(0, weight=1)
        self.summary = ttk.Label(footer, style="Muted.TLabel")
        self.summary.grid(row=0, column=0, sticky="w")
        self.output_button = ttk.Button(footer, text="打开输出", command=open_output)
        self.output_button.grid(row=0, column=1, padx=(8, 0))
        self.report_button = ttk.Button(footer, text="打开报告", command=open_report)
        self.report_button.grid(row=0, column=2, padx=(8, 0))
        self.refresh()

    def refresh(self) -> None:
        current = self.state.selected_key
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)
        for source in self.state.sources:
            item = self.state.results.get(str(source))
            status = item.status if item else BatchStatus.PENDING
            self.tree.insert(
                "",
                "end",
                iid=str(source),
                values=(
                    source.name,
                    TYPE_TEXT.get(source.suffix.lower(), "Office"),
                    self._file_size(source),
                    STATUS_TEXT[status],
                ),
                tags=(self._tag(status),),
            )
        if current and self.tree.exists(current):
            self.tree.selection_set(current)
        self.summary.configure(text=f"{len(self.state.sources)} 个文件")
        available = bool(self.state.selected_item and self.state.selected_item.result)
        self.output_button.state(("!disabled" if available else "disabled",))
        self.report_button.state(("!disabled" if available else "disabled",))

    def set_editable(self, editable: bool) -> None:
        state = "!disabled" if editable else "disabled"
        self.recursive.state((state,))
        for child in self.winfo_children()[0].winfo_children():
            if isinstance(child, ttk.Button):
                child.state((state,))

    def _on_select(self, _event: tk.Event[tk.Misc]) -> None:
        selection = self.tree.selection()
        self.state.selected_key = selection[0] if selection else None
        self.refresh()

    @staticmethod
    def _file_size(path: Path) -> str:
        try:
            size = path.stat().st_size
        except OSError:
            return "未知"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"

    @staticmethod
    def _tag(status: BatchStatus) -> str:
        if status is BatchStatus.SUCCESS:
            return "success"
        if status is BatchStatus.WARNING:
            return "warning"
        if status is BatchStatus.FAILED:
            return "failed"
        if status is BatchStatus.RUNNING:
            return "running"
        return "muted"
