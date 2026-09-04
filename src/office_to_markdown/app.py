from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .batch import BatchConversionService, discover_sources
from .models import BatchItem, BatchResult, BatchStatus, ConversionOptions
from .security import ValidationError, validate_tags
from .settings import SettingsStore


class MainWindow:
    """Local-first Tkinter desktop UI for Office to Markdown conversion.

    The UI keeps the visual language established in v0.3 (rounded cards,
    self-drawn buttons and status pills) while using the native Windows title
    bar for reliable resizing, snapping and window controls.
    """

    COLORS = {
        "page": "#EFF1F5",
        "card": "#FFFFFF",
        "primary": "#3660F4",
        "primary_hover": "#2952D6",
        "secondary": "#E7EDFE",
        "secondary_hover": "#D4DDFA",
        "quiet": "#F3F4F8",
        "quiet_hover": "#E6E8F0",
        "text": "#181818",
        "body": "#4D4D4D",
        "muted": "#808080",
        "input": "#F3F4F8",
        "input_hover": "#E6E8F0",
        "line": "#EDF0F7",
        "line_hover": "#D8DEEA",
        "success": "#09B42C",
        "success_bg": "#E5F7E9",
        "warning": "#FF8719",
        "warning_bg": "#FFF3E6",
        "wait": "#808080",
        "wait_bg": "#F0F1F5",
        "error": "#FA5151",
        "error_bg": "#FFE8E8",
        "selected": "#F0F4FF",
        "row_hover": "#F8F9FC",
    }
    FONT = "Noto Sans SC"

    CARD_MARGIN = 16
    CARD_RADIUS = 12
    BUTTON_RADIUS = 8
    BUTTON_HEIGHT = 36
    CHECK_SIZE = 18
    QUEUE_ROW_HEIGHT = 48
    BOTTOM_BAR_HEIGHT = 64
    ANIMATION_MS = 100

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("廾匸转换")
        self.root.overrideredirect(False)
        self.root.resizable(True, True)
        self.root.minsize(1040, 760)
        self.root.geometry("1280x800")

        self.settings = SettingsStore()
        default_output = self.settings.load_default_output()
        self.output = tk.StringVar(value=str(default_output) if default_output else "")
        self.tags = tk.StringVar()
        self.vault_root = tk.StringVar()
        self.recursive = tk.BooleanVar(value=True)
        self.obsidian = tk.BooleanVar(value=False)
        self.include_source_link = tk.BooleanVar(value=False)
        self.copy_source = tk.BooleanVar(value=False)
        self.export_pptx_png = tk.BooleanVar(value=False)
        self.export_pptx_pdf = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="尚未添加文件，文件仅在本机处理。")

        self.sources: list[Path] = []
        self.worker: BatchConversionService | None = None
        self.events: queue.Queue[BatchResult | Exception] = queue.Queue()
        self.results: dict[str, BatchItem] = {}
        self.selected_key: str | None = None
        self.hitboxes: list[tuple[str, tuple[int, int, int, int]]] = []
        self._hover_key: str | None = None
        self._queue_hover_key: str | None = None
        self._progress_phase: int = 0
        self._last_size: tuple[int, int] = (1280, 800)

        self.canvas = tk.Canvas(
            self.root,
            background=self.COLORS["page"],
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self.output_entry = self._entry(self.output)
        self.tags_entry = self._entry(self.tags)
        self.vault_entry = self._entry(self.vault_root)

        self._build_queue_viewport()

        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Button-1>", self._click)
        self.canvas.bind("<Motion>", self._hover)
        self.root.bind("<Escape>", lambda _event: self.root.destroy())

        self._draw()
        self.root.after(100, self._poll_events)
        self.root.after(self.ANIMATION_MS, self._animate_progress)

    def _entry(self, variable: tk.StringVar) -> tk.Entry:
        return tk.Entry(
            self.root,
            textvariable=variable,
            relief="flat",
            borderwidth=0,
            background=self.COLORS["input"],
            foreground=self.COLORS["body"],
            insertbackground=self.COLORS["text"],
            font=(self.FONT, 11),
        )

    def _build_queue_viewport(self) -> None:
        """Create an independent scrollable viewport for the file queue."""
        self.queue_frame = tk.Frame(self.root, background=self.COLORS["card"])
        self.queue_canvas = tk.Canvas(
            self.queue_frame,
            background=self.COLORS["card"],
            highlightthickness=0,
            borderwidth=0,
        )
        self.queue_scrollbar = ttk.Scrollbar(
            self.queue_frame,
            orient="vertical",
            command=self._on_queue_scroll,
        )
        self.queue_canvas.configure(yscrollcommand=self.queue_scrollbar.set)
        self.queue_scrollbar.pack(side="right", fill="y")
        self.queue_canvas.pack(side="left", fill="both", expand=True)

        self.queue_frame.bind("<MouseWheel>", self._on_mousewheel)
        self.queue_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.queue_canvas.bind("<Button-1>", self._queue_click)
        self.queue_canvas.bind("<Motion>", self._queue_hover)

    def _on_queue_scroll(self, *args: object) -> None:
        self.queue_canvas.yview(*args)
        self._draw_queue()

    def _on_mousewheel(self, event: tk.Event[tk.Misc]) -> None:
        self.queue_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self._draw_queue()

    def _on_configure(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        width, height = self.root.winfo_width(), self.root.winfo_height()
        if (width, height) != self._last_size:
            self._last_size = (width, height)
            self._draw()
        else:
            # Geometry changes from create_window can also fire Configure.
            self._draw_queue()

    def _round(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        radius: int,
        fill: str,
        outline: str = "",
    ) -> None:
        self.canvas.create_polygon(
            x1 + radius,
            y1,
            x2 - radius,
            y1,
            x2,
            y1,
            x2,
            y1 + radius,
            x2,
            y2 - radius,
            x2 - radius,
            y2,
            x1 + radius,
            y2,
            x1,
            y2 - radius,
            x1,
            y1 + radius,
            smooth=True,
            splinesteps=20,
            fill=fill,
            outline=outline,
        )

    def _round_on_canvas(
        self,
        canvas: tk.Canvas,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        radius: int,
        fill: str,
        outline: str = "",
    ) -> None:
        canvas.create_polygon(
            x1 + radius,
            y1,
            x2 - radius,
            y1,
            x2,
            y1,
            x2,
            y1 + radius,
            x2,
            y2 - radius,
            x2 - radius,
            y2,
            x1 + radius,
            y2,
            x1,
            y2 - radius,
            x1,
            y1 + radius,
            smooth=True,
            splinesteps=20,
            fill=fill,
            outline=outline,
        )

    def _text(
        self,
        x: int,
        y: int,
        text: str,
        size: int = 13,
        color: str | None = None,
        bold: bool = False,
        anchor: str = "w",
    ) -> None:
        self.canvas.create_text(
            x,
            y,
            text=text,
            anchor=anchor,
            fill=color or self.COLORS["body"],
            font=(self.FONT, size, "bold" if bold else "normal"),
        )

    def _button(
        self,
        key: str,
        x: int,
        y: int,
        width: int,
        text: str,
        primary: bool = False,
        quiet: bool = False,
        enabled: bool = True,
    ) -> None:
        is_hovered = self._hover_key == key and enabled
        if not enabled:
            fill, color = self.COLORS["line"], self.COLORS["muted"]
        elif primary:
            fill = self.COLORS["primary_hover"] if is_hovered else self.COLORS["primary"]
            color = "#FFFFFF"
        elif quiet:
            fill = self.COLORS["quiet_hover"] if is_hovered else self.COLORS["quiet"]
            color = self.COLORS["body"]
        else:
            fill = self.COLORS["secondary_hover"] if is_hovered else self.COLORS["secondary"]
            color = self.COLORS["primary"]

        self._round(x, y, x + width, y + self.BUTTON_HEIGHT, self.BUTTON_RADIUS, fill)
        self.canvas.create_text(
            x + width // 2,
            y + self.BUTTON_HEIGHT // 2,
            text=text,
            fill=color,
            font=(self.FONT, 12, "bold" if not quiet else "normal"),
        )
        if enabled:
            self.hitboxes.append((key, (x, y, x + width, y + self.BUTTON_HEIGHT)))

    def _check(
        self,
        key: str,
        x: int,
        y: int,
        variable: tk.BooleanVar,
        label: str,
        enabled: bool = True,
    ) -> None:
        is_hovered = self._hover_key == key and enabled
        size = self.CHECK_SIZE
        if not enabled:
            border_color = self.COLORS["line"]
            bg_color = self.COLORS["quiet"]
        elif variable.get():
            border_color = self.COLORS["primary"]
            bg_color = self.COLORS["primary"]
        elif is_hovered:
            border_color = self.COLORS["primary"]
            bg_color = self.COLORS["input_hover"]
        else:
            border_color = self.COLORS["line"]
            bg_color = self.COLORS["input"]

        self._round(x, y, x + size, y + size, 4, border_color)
        self._round(x + 1, y + 1, x + size - 1, y + size - 1, 3, bg_color)
        if variable.get():
            self.canvas.create_text(
                x + size // 2,
                y + size // 2,
                text="✓",
                fill="#FFFFFF",
                font=("Segoe UI", 11, "bold"),
            )
        self._text(
            x + size + 8,
            y + size // 2,
            label,
            12,
            self.COLORS["body"] if enabled else self.COLORS["muted"],
        )
        if enabled:
            label_width = len(label) * 13 + size + 12
            self.hitboxes.append((key, (x, y - 4, x + label_width, y + size + 4)))

    def _pill(self, x: int, y: int, text: str, color: str, background: str) -> None:
        width = len(text) * 12 + 24
        self._round(x, y, x + width, y + 30, 15, background)
        self.canvas.create_text(
            x + width // 2,
            y + 15,
            text=text,
            fill=color,
            font=(self.FONT, 11, "bold"),
        )

    def _card(self, x: int, y: int, width: int, height: int, title: str) -> None:
        self._round(x, y, x + width, y + height, self.CARD_RADIUS, self.COLORS["card"])
        self._text(x + 20, y + 25, title, 16, self.COLORS["text"], True)

    def _draw(self) -> None:
        self.canvas.delete("all")
        self._sync_option_states()
        width = max(1040, self.root.winfo_width())
        height = max(760, self.root.winfo_height())
        self.hitboxes.clear()

        self._draw_header(width)

        margin = self.CARD_MARGIN
        card_width = width - 2 * margin

        import_y = 92
        import_h = 112
        self._draw_import(margin, import_y, card_width, import_h, width)

        rules_y = import_y + import_h + margin
        rules_h = 180
        self._draw_rules(margin, rules_y, card_width, rules_h, width)

        queue_y = rules_y + rules_h + margin
        queue_h = height - queue_y - self.BOTTOM_BAR_HEIGHT - margin
        self._draw_queue_card(margin, queue_y, card_width, queue_h, width)

        self._draw_bottom_bar(width, height)

    def _sync_option_states(self) -> None:
        state = "normal" if self.obsidian.get() else "disabled"
        self.tags_entry.configure(state=state)
        self.vault_entry.configure(state=state)

    def _draw_header(self, width: int) -> None:
        self._text(self.CARD_MARGIN, 34, "廾匸转换", 22, self.COLORS["text"], True)
        self._text(self.CARD_MARGIN, 62, "Office 文件转 Markdown", 13, self.COLORS["muted"])
        self._pill(
            width - 218,
            32,
            "本地处理 · 不上传文件",
            self.COLORS["primary"],
            self.COLORS["secondary"],
        )

    def _draw_import(self, x: int, y: int, width: int, height: int, page_width: int) -> None:
        self._card(x, y, width, height, "导入文件")
        self._text(
            x + 20,
            y + 58,
            "选择需要归档的 Word、PowerPoint 或 Excel 文件。可重复添加，按队列顺序处理。",
            12,
            self.COLORS["muted"],
        )
        self._button("files", x + 20, y + 86, 126, "选择文件", True)
        self._button("folder", x + 162, y + 86, 144, "扫描文件夹")
        self._check("recursive", page_width - 178, y + 92, self.recursive, "包含子文件夹")

    def _draw_rules(self, x: int, y: int, width: int, height: int, page_width: int) -> None:
        self._card(x, y, width, height, "输出规则")
        mid_x = x + width // 2
        self.canvas.create_line(
            mid_x,
            y + 45,
            mid_x,
            y + height - 20,
            fill=self.COLORS["line"],
            width=1,
        )

        left_x = x + 20
        left_w = mid_x - left_x - 20
        self._text(left_x, y + 58, "保存到", 13, self.COLORS["body"], True)

        entry_y = y + 78
        entry_w = max(200, left_w - 244)
        self._round(left_x, entry_y, left_x + entry_w, entry_y + 36, 8, self.COLORS["input"])
        self.canvas.create_window(
            left_x + 12,
            entry_y + 18,
            window=self.output_entry,
            anchor="w",
            width=entry_w - 24,
            height=30,
        )
        self._button("output", left_x + entry_w + 12, entry_y, 112, "选择位置")
        self._button("default", left_x + entry_w + 136, entry_y, 108, "设为默认", quiet=True)

        right_x = mid_x + 20
        right_w = x + width - right_x - 20

        row1_y = y + 58
        self._check("obsidian", right_x, row1_y, self.obsidian, "Obsidian 模式")
        self._text(right_x + 136, row1_y + 8, "标签", 12, self.COLORS["muted"])
        if self.obsidian.get():
            tag_x = right_x + 174
            tag_w = max(120, min(180, right_w - 174 - 12))
            self._round(tag_x, row1_y - 9, tag_x + tag_w, row1_y + 27, 8, self.COLORS["input"])
            self.canvas.create_window(
                tag_x + 10,
                row1_y + 9,
                window=self.tags_entry,
                anchor="w",
                width=tag_w - 20,
                height=30,
            )
        else:
            self._text(right_x + 174, row1_y + 8, "启用后可设置", 12, self.COLORS["muted"])

        row2_y = y + 102
        self._check(
            "source-link",
            right_x,
            row2_y,
            self.include_source_link,
            "添加原文件链接",
            self.obsidian.get(),
        )
        vault_x = right_x + 150
        vault_w = max(120, right_w - 150 - 124)
        if self.obsidian.get():
            self._round(
                vault_x, row2_y - 9, vault_x + vault_w, row2_y + 27, 8, self.COLORS["input"]
            )
            self.canvas.create_window(
                vault_x + 10,
                row2_y + 9,
                window=self.vault_entry,
                anchor="w",
                width=vault_w - 20,
                height=30,
            )
        self._button(
            "vault",
            vault_x + vault_w + 12,
            row2_y - 9,
            112,
            "选择 Vault",
            enabled=self.obsidian.get(),
        )

        row3_y = y + 146
        self._check(
            "copy",
            right_x,
            row3_y,
            self.copy_source,
            "复制原文件到输出目录",
            self.obsidian.get(),
        )
        pptx_x = right_x + 224
        if pptx_x + 260 <= x + width - 20:
            self._text(pptx_x, row3_y + 8, "PPTX 视觉附件", 13, self.COLORS["body"], True)
            self._check("png", pptx_x + 122, row3_y, self.export_pptx_png, "每页 PNG")
            self._check("pdf", pptx_x + 216, row3_y, self.export_pptx_pdf, "版式 PDF")

    def _draw_queue_card(self, x: int, y: int, width: int, height: int, page_width: int) -> None:
        self._card(x, y, width, height, "待处理文件")

        progress = (
            sum(item.status == BatchStatus.SUCCESS for item in self.results.values())
            / len(self.sources)
            if self.sources
            else 0
        )
        meta = (
            f"{len(self.sources)} 个文件 · 整体进度 {progress:.0%}"
            if self.sources
            else "尚未添加文件"
        )
        self._text(page_width - 36, y + 25, meta, 12, self.COLORS["muted"], anchor="e")

        bar_y = y + 48
        self._round(36, bar_y, page_width - 36, bar_y + 8, 4, self.COLORS["line"])
        if progress > 0:
            self._round(
                36,
                bar_y,
                int(36 + (page_width - 72) * progress),
                bar_y + 8,
                4,
                self.COLORS["primary"],
            )
        elif self.worker and any(
            item.status == BatchStatus.RUNNING for item in self.results.values()
        ):
            self._draw_animated_bar(36, bar_y, page_width - 36)

        viewport_x = 36
        viewport_y = y + 72
        viewport_w = page_width - 72
        viewport_h = max(40, height - 88)

        self.canvas.create_window(
            viewport_x,
            viewport_y,
            window=self.queue_frame,
            anchor="nw",
            width=viewport_w,
            height=viewport_h,
        )

        self._draw_queue()

    def _draw_animated_bar(self, x1: int, y1: int, x2: int) -> None:
        total = x2 - x1
        segment = total // 5
        offset = (self._progress_phase * segment) // 20
        for index in range(-1, 6):
            sx = x1 + ((index * segment + offset) % total)
            ex = min(x2, sx + segment // 2)
            if ex > sx:
                self._round(sx, y1, ex, y1 + 8, 4, self.COLORS["secondary"])

    def _draw_queue(self) -> None:
        canvas = self.queue_canvas
        canvas.delete("all")
        viewport_w = max(40, self.queue_canvas.winfo_width())
        viewport_h = max(40, self.queue_canvas.winfo_height())

        if not self.sources:
            canvas.create_text(
                viewport_w // 2,
                viewport_h // 2,
                text="选择文件或扫描文件夹后，文件会按添加顺序显示在这里。",
                fill=self.COLORS["muted"],
                font=(self.FONT, 13),
            )
            self.queue_scrollbar.pack_forget()
            return

        total_height = len(self.sources) * self.QUEUE_ROW_HEIGHT
        canvas.config(scrollregion=(0, 0, viewport_w, total_height))

        if total_height > viewport_h:
            self.queue_scrollbar.pack(side="right", fill="y")
        else:
            self.queue_scrollbar.pack_forget()

        offset = int(canvas.yview()[0] * max(1, total_height - viewport_h))

        for index, source in enumerate(self.sources):
            row_y = index * self.QUEUE_ROW_HEIGHT - offset
            if row_y + self.QUEUE_ROW_HEIGHT < 0 or row_y > viewport_h:
                continue
            self._draw_file_row(canvas, 0, row_y, viewport_w, source)

    def _draw_file_row(
        self,
        canvas: tk.Canvas,
        x: int,
        y: int,
        width: int,
        source: Path,
    ) -> None:
        key = str(source)
        item = self.results.get(key)
        mapping = {
            BatchStatus.RUNNING: ("转换中", self.COLORS["primary"], self.COLORS["secondary"]),
            BatchStatus.SUCCESS: ("已完成", self.COLORS["success"], self.COLORS["success_bg"]),
            BatchStatus.WARNING: ("有警告", self.COLORS["warning"], self.COLORS["warning_bg"]),
            BatchStatus.FAILED: ("转换失败", self.COLORS["error"], self.COLORS["error_bg"]),
            BatchStatus.CANCELLED: ("已取消", self.COLORS["wait"], self.COLORS["wait_bg"]),
        }
        state, color, background = (
            mapping.get(item.status, ("等待中", self.COLORS["wait"], self.COLORS["wait_bg"]))
            if item
            else ("等待中", self.COLORS["wait"], self.COLORS["wait_bg"])
        )
        detail = (
            item.error_message if item and item.error_message else self._source_detail(source)
        )

        if key == self.selected_key:
            self._round_on_canvas(
                canvas, x, y, x + width, y + self.QUEUE_ROW_HEIGHT, 8, self.COLORS["selected"]
            )
        elif key == self._queue_hover_key:
            self._round_on_canvas(
                canvas, x, y, x + width, y + self.QUEUE_ROW_HEIGHT, 8, self.COLORS["row_hover"]
            )

        badge, badge_color = self._file_badge(source)
        self._round_on_canvas(canvas, x, y + 9, x + 30, y + 39, 8, badge_color)
        canvas.create_text(
            x + 15,
            y + 24,
            text=badge,
            fill="#FFFFFF",
            font=(self.FONT, 12, "bold"),
        )

        name_w = width - 44 - 110
        canvas.create_text(
            x + 44,
            y + 16,
            text=source.name,
            fill=self.COLORS["text"],
            font=(self.FONT, 13, "bold"),
            anchor="w",
            width=name_w,
        )
        canvas.create_text(
            x + 44,
            y + 34,
            text=detail,
            fill=self.COLORS["muted"],
            font=(self.FONT, 12),
            anchor="w",
        )

        pill_width = max(72, len(state) * 12 + 24)
        pill_x = x + width - pill_width
        self._round_on_canvas(canvas, pill_x, y + 9, x + width, y + 39, 15, background)
        canvas.create_text(
            pill_x + pill_width // 2,
            y + 24,
            text=state,
            fill=color,
            font=(self.FONT, 11, "bold"),
        )

    def _file_badge(self, source: Path) -> tuple[str, str]:
        return {
            ".docx": ("W", "#2B579A"),
            ".pptx": ("P", "#D24726"),
            ".xlsx": ("X", "#217346"),
        }.get(source.suffix.lower(), ("?", self.COLORS["wait"]))

    def _source_detail(self, source: Path) -> str:
        try:
            size = f"{source.stat().st_size / (1024 * 1024):.1f} MB"
        except OSError:
            size = "大小未知"
        kind = {
            ".docx": "Word 文档",
            ".pptx": "PowerPoint 演示",
            ".xlsx": "Excel 表格",
        }.get(source.suffix.lower(), "Office 文件")
        return f"{size} · {kind}"

    def _draw_bottom_bar(self, width: int, height: int) -> None:
        y = height - self.BOTTOM_BAR_HEIGHT
        self._round(16, y + 8, width - 16, y + self.BOTTOM_BAR_HEIGHT - 8, 12, self.COLORS["card"])

        can_start = bool(self.sources) and self.worker is None
        self._button("start", 28, y + 14, 138, "开始处理", True, enabled=can_start)
        self._button("cancel", 176, y + 14, 122, "取消队列", quiet=True, enabled=bool(self.worker))

        self.canvas.create_text(
            width // 2,
            y + 32,
            text=self.status.get(),
            fill=self.COLORS["muted"],
            font=(self.FONT, 12),
        )

        selected = self._selected_result()
        can_open = bool(selected and selected.result)
        self._button("report", width - 272, y + 14, 120, "打开选中报告", enabled=can_open)
        self._button("open", width - 138, y + 14, 120, "打开选中输出", enabled=can_open)

    def _hover(self, event: tk.Event[tk.Misc]) -> None:
        previous = self._hover_key
        self._hover_key = None
        for key, (x1, y1, x2, y2) in reversed(self.hitboxes):
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self._hover_key = key
                break
        self.canvas.configure(cursor="hand2" if self._hover_key else "")
        if self._hover_key != previous:
            self._draw()

    def _queue_hover(self, event: tk.Event[tk.Misc]) -> None:
        previous = self._queue_hover_key
        self._queue_hover_key = None
        canvas = self.queue_canvas
        viewport_w = max(40, canvas.winfo_width())
        if not self.sources:
            return
        total_height = len(self.sources) * self.QUEUE_ROW_HEIGHT
        viewport_h = max(40, canvas.winfo_height())
        offset = int(canvas.yview()[0] * max(1, total_height - viewport_h))
        for index, source in enumerate(self.sources):
            row_y = index * self.QUEUE_ROW_HEIGHT - offset
            if row_y + self.QUEUE_ROW_HEIGHT < 0 or row_y > viewport_h:
                continue
            if 0 <= event.x <= viewport_w and row_y <= event.y <= row_y + self.QUEUE_ROW_HEIGHT:
                self._queue_hover_key = str(source)
                canvas.configure(cursor="hand2")
                break
        else:
            canvas.configure(cursor="")
        if self._queue_hover_key != previous:
            self._draw_queue()

    def _click(self, event: tk.Event[tk.Misc]) -> None:
        for key, (x1, y1, x2, y2) in reversed(self.hitboxes):
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self._dispatch(key)
                return

    def _queue_click(self, event: tk.Event[tk.Misc]) -> None:
        canvas = self.queue_canvas
        viewport_w = max(40, canvas.winfo_width())
        if not self.sources:
            return
        total_height = len(self.sources) * self.QUEUE_ROW_HEIGHT
        viewport_h = max(40, canvas.winfo_height())
        offset = int(canvas.yview()[0] * max(1, total_height - viewport_h))
        for index, source in enumerate(self.sources):
            row_y = index * self.QUEUE_ROW_HEIGHT - offset
            if row_y + self.QUEUE_ROW_HEIGHT < 0 or row_y > viewport_h:
                continue
            if 0 <= event.x <= viewport_w and row_y <= event.y <= row_y + self.QUEUE_ROW_HEIGHT:
                self.selected_key = str(source)
                self._draw_queue()
                self._draw_bottom_bar(self.root.winfo_width(), self.root.winfo_height())
                return

    def _dispatch(self, key: str) -> None:
        toggles = {
            "recursive": self.recursive,
            "obsidian": self.obsidian,
            "source-link": self.include_source_link,
            "copy": self.copy_source,
            "png": self.export_pptx_png,
            "pdf": self.export_pptx_pdf,
        }
        if key in toggles:
            toggles[key].set(not toggles[key].get())
        elif key == "files":
            self.choose_files()
        elif key == "folder":
            self.choose_folder()
        elif key == "output":
            self.choose_output()
        elif key == "default":
            self.save_default_output()
        elif key == "vault":
            self.choose_vault()
        elif key == "start":
            self.start()
        elif key == "cancel":
            self.cancel()
        elif key == "report":
            self.open_selected_report()
        elif key == "open":
            self.open_selected_output()
        self._draw()

    def choose_files(self) -> None:
        self._add_sources(
            Path(path)
            for path in filedialog.askopenfilenames(
                filetypes=[("Office 文件", "*.docx *.pptx *.xlsx")]
            )
        )

    def choose_folder(self) -> None:
        selected = filedialog.askdirectory()
        if selected:
            self._add_sources(discover_sources(Path(selected), self.recursive.get()))

    def _add_sources(self, paths) -> None:
        existing = set(self.sources)
        for path in paths:
            if path not in existing:
                self.sources.append(path)
                existing.add(path)
        self.status.set(f"已加入 {len(self.sources)} 个文件，文件仅在本机处理。")
        self._draw()

    def choose_output(self) -> None:
        selected = filedialog.askdirectory()
        if selected:
            self.output.set(selected)
            self._draw()

    def save_default_output(self) -> None:
        output = Path(self.output.get())
        if not output.is_dir():
            messagebox.showerror("无法保存", "请选择一个已存在的输出目录。")
            return
        try:
            self.settings.save_default_output(output)
        except OSError:
            messagebox.showerror("无法保存", "默认输出目录设置保存失败。")
            return
        self.status.set("已保存默认输出目录。")
        self._draw()

    def choose_vault(self) -> None:
        selected = filedialog.askdirectory()
        if selected:
            self.vault_root.set(selected)
            self._draw()

    def start(self) -> None:
        if not self.sources:
            messagebox.showerror("无法开始", "请先添加 Office 文件。")
            return
        try:
            output = Path(self.output.get())
            if not output.is_dir():
                raise ValidationError("请选择一个已存在的输出目录。")
            tags = tuple(tag.strip() for tag in self.tags.get().split(",") if tag.strip())
            if self.obsidian.get() and not tags:
                tags = ("office-import",)
            validate_tags(tags)
            root = Path(self.vault_root.get()) if self.vault_root.get() else None
            if self.include_source_link.get() and root is None:
                raise ValidationError("添加原文件链接时请先选择 Vault 根目录。")
            if self.copy_source.get() and not self.obsidian.get():
                raise ValidationError("复制原文件仅可在 Obsidian 模式中启用。")
            options = ConversionOptions(
                obsidian_mode=self.obsidian.get(),
                include_frontmatter=self.obsidian.get(),
                tags=tags,
                include_source_link=self.include_source_link.get(),
                source_link_root=root,
                copy_source=self.copy_source.get(),
                export_pptx_png=self.export_pptx_png.get(),
                export_pptx_pdf=self.export_pptx_pdf.get(),
            )
        except (ValidationError, ValueError) as error:
            messagebox.showerror("无法开始", str(error))
            return
        self.results.clear()
        self.worker = BatchConversionService()
        self.status.set("正在后台处理，请稍候。")
        threading.Thread(
            target=self._run_batch, args=(tuple(self.sources), output, options), daemon=True
        ).start()
        self._draw()

    def _run_batch(
        self, sources: tuple[Path, ...], output: Path, options: ConversionOptions
    ) -> None:
        try:
            self.events.put(
                self.worker.convert(sources, output, options, self.events.put)
                if self.worker
                else RuntimeError()
            )
        except Exception as error:
            self.events.put(error)

    def cancel(self) -> None:
        if self.worker:
            self.worker.cancel()
            self.status.set("将在当前文件完成后取消剩余队列。")
            self._draw()

    def _poll_events(self) -> None:
        try:
            event = self.events.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll_events)
            return
        if isinstance(event, BatchItem):
            self.results[str(event.source_path)] = event
        elif isinstance(event, Exception):
            messagebox.showerror("转换失败", "批处理发生意外错误。")
            self.status.set("批处理失败。")
        else:
            self._show_result(event)
        self._draw()
        self.root.after(100, self._poll_events)

    def _show_result(self, result: BatchResult) -> None:
        labels = {
            BatchStatus.SUCCESS: "成功",
            BatchStatus.WARNING: "警告",
            BatchStatus.FAILED: "失败",
            BatchStatus.SKIPPED: "跳过",
            BatchStatus.CANCELLED: "取消",
        }
        for item in result.items:
            self.results[str(item.source_path)] = item
        self.status.set(
            "处理完成："
            + "，".join(
                f"{labels[state]}: {result.count(state)}" for state in labels if result.count(state)
            )
        )

    def _selected_result(self) -> BatchItem | None:
        return self.results.get(self.selected_key) if self.selected_key else None

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

    def _animate_progress(self) -> None:
        self._progress_phase = (self._progress_phase + 1) % 20
        if self.worker and any(
            item.status == BatchStatus.RUNNING for item in self.results.values()
        ):
            self._draw()
        self.root.after(self.ANIMATION_MS, self._animate_progress)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    MainWindow().run()
