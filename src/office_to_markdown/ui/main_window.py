from __future__ import annotations

# ruff: noqa: E501
import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ..batch import BatchConversionService, discover_sources
from ..models import BatchItem, BatchResult, BatchStatus, ConversionOptions
from ..security import ValidationError
from ..settings import SettingsStore
from .queue_panel import QueuePanel
from .settings_panel import SettingsPanel
from .state import UiPhase, UiState
from .status_bar import StatusBar
from .theme import apply_theme


class MainWindow:
    """Local-first Tkinter/ttk workbench that delegates conversion to existing services."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("廾匸转换")
        self.root.overrideredirect(False)
        self.root.resizable(True, True)
        self.root.minsize(1040, 760)
        self.root.geometry("1280x800")
        apply_theme(self.root)
        self.settings = SettingsStore()
        self.state = UiState(self.root, self.settings.load_default_output())
        self.worker: BatchConversionService | None = None
        self.events: queue.Queue[BatchItem | BatchResult | Exception] = queue.Queue()
        self._build()
        self.root.after(100, self._poll_events)

    @property
    def sources(self) -> list[Path]:
        return self.state.sources

    @sources.setter
    def sources(self, value: list[Path]) -> None:
        self.state.sources = value

    @property
    def results(self) -> dict[str, BatchItem]:
        return self.state.results

    @property
    def selected_key(self) -> str | None:
        return self.state.selected_key

    @selected_key.setter
    def selected_key(self, value: str | None) -> None:
        self.state.selected_key = value

    def _build(self) -> None:
        shell = ttk.Frame(self.root, style="App.TFrame", padding=16)
        shell.pack(fill="both", expand=True)
        shell.columnconfigure(0, weight=3, minsize=580)
        shell.columnconfigure(1, weight=2, minsize=330)
        shell.rowconfigure(1, weight=1)
        header = ttk.Frame(shell, style="App.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="廾匸转换", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="本地文档转 Markdown", style="Body.TLabel").grid(
            row=1, column=0, sticky="w"
        )
        ttk.Label(header, text="本地处理，不上传文件", style="Body.TLabel").grid(
            row=0, column=1, rowspan=2, sticky="e"
        )
        self.queue_panel = QueuePanel(
            shell,
            self.state,
            self.choose_files,
            self.choose_folder,
            self.open_selected_output,
            self.open_selected_report,
        )
        self.queue_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        self.settings_panel = SettingsPanel(
            shell, self.state, self.choose_output, self.save_default_output, self.choose_vault
        )
        self.settings_panel.grid(row=1, column=1, sticky="nsew")
        self.status_bar = StatusBar(shell, self.state, self.start, self.cancel)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        self.refresh()

    def refresh(self) -> None:
        self.queue_panel.refresh()
        self.queue_panel.set_editable(self.state.can_edit)
        self.settings_panel.set_editable(self.state.can_edit)
        self.status_bar.refresh()

    def choose_files(self) -> None:
        selected = filedialog.askopenfilenames(
            filetypes=[
                ("支持的文件", "*.docx *.pptx *.xlsx *.pdf *.txt"),
                ("Office 文档", "*.docx *.pptx *.xlsx"),
                ("PDF 文件", "*.pdf"),
                ("文本文件", "*.txt"),
            ]
        )
        self._add_sources(Path(path) for path in selected)

    def choose_folder(self) -> None:
        selected = filedialog.askdirectory()
        if selected:
            self._add_sources(discover_sources(Path(selected), self.state.recursive.get()))

    def _add_sources(self, paths) -> None:
        self.state.add_sources(list(paths))
        self.state.status.set(f"已加入 {len(self.sources)} 个文件，文件仅在本机处理。")
        self.refresh()

    def choose_output(self) -> None:
        selected = filedialog.askdirectory()
        if selected:
            self.state.output.set(selected)
            self.refresh()

    def save_default_output(self) -> None:
        output = Path(self.state.output.get())
        if not output.is_dir():
            messagebox.showerror("无法保存", "请选择一个已存在的输出目录。")
            return
        try:
            self.settings.save_default_output(output)
        except OSError:
            messagebox.showerror("无法保存", "默认输出目录设置保存失败。")
            return
        self.state.status.set("已保存默认输出目录。")
        self.refresh()

    def choose_vault(self) -> None:
        selected = filedialog.askdirectory()
        if selected:
            self.state.vault_root.set(selected)
            self.refresh()

    def start(self) -> None:
        if not self.sources:
            messagebox.showerror("无法开始", "请先添加支持的文件。")
            return
        try:
            output = Path(self.state.output.get())
            if not output.is_dir():
                raise ValidationError("请选择一个已存在的输出目录。")
            options = self.state.build_options()
        except (ValidationError, ValueError) as error:
            messagebox.showerror("无法开始", str(error))
            return
        self.state.results.clear()
        self.worker = BatchConversionService()
        self.state.set_phase(UiPhase.RUNNING)
        self.state.status.set("正在后台处理，请稍候。")
        threading.Thread(
            target=self._run_batch, args=(tuple(self.sources), output, options), daemon=True
        ).start()
        self.refresh()

    def _run_batch(
        self, sources: tuple[Path, ...], output: Path, options: ConversionOptions
    ) -> None:
        try:
            if self.worker:
                self.events.put(self.worker.convert(sources, output, options, self.events.put))
        except Exception as error:
            self.events.put(error)

    def cancel(self) -> None:
        if self.worker and self.state.phase is UiPhase.RUNNING:
            self.worker.cancel()
            self.state.set_phase(UiPhase.CANCELLING)
            self.state.status.set("当前文件完成后停止。")
            self.refresh()

    def _poll_events(self) -> None:
        try:
            event = self.events.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll_events)
            return
        if isinstance(event, BatchItem):
            self.state.apply_item(event)
            self.state.status.set(f"正在处理：{event.source_path.name}")
        elif isinstance(event, Exception):
            self.worker = None
            self.state.set_phase(UiPhase.COMPLETED)
            self.state.status.set("批处理发生意外错误。")
            messagebox.showerror("转换失败", "批处理发生意外错误。")
        else:
            self._show_result(event)
        self.refresh()
        self.root.after(100, self._poll_events)

    def _show_result(self, result: BatchResult) -> None:
        self.state.apply_result(result)
        self.worker = None
        self.state.set_phase(UiPhase.COMPLETED)
        labels = {
            BatchStatus.SUCCESS: "成功",
            BatchStatus.WARNING: "警告",
            BatchStatus.FAILED: "失败",
            BatchStatus.SKIPPED: "跳过",
            BatchStatus.CANCELLED: "取消",
        }
        self.state.status.set(
            "处理完成："
            + "，".join(
                f"{labels[item]}: {result.count(item)}" for item in labels if result.count(item)
            )
        )

    def _selected_result(self) -> BatchItem | None:
        return self.state.selected_item

    def _open_path(self, path: Path) -> None:
        if path.exists():
            os.startfile(path)  # type: ignore[attr-defined]

    def open_selected_output(self) -> None:
        item = self._selected_result()
        if item and item.result:
            self._open_path(item.result.output_path)

    def open_selected_report(self) -> None:
        item = self._selected_result()
        if item and item.result:
            self._open_path(item.result.report_path)

    def run(self) -> None:
        self.root.mainloop()
