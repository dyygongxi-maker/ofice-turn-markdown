from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from .batch import BatchConversionService, discover_sources
from .models import BatchItem, BatchResult, BatchStatus, ConversionOptions
from .security import ValidationError, validate_tags
from .settings import SettingsStore


class MainWindow:
    COLORS = {
        "page": "#EFF1F5",
        "card": "#FFFFFF",
        "primary": "#3660F4",
        "secondary": "#E7EDFE",
        "quiet": "#F3F4F8",
        "text": "#181818",
        "body": "#4D4D4D",
        "muted": "#808080",
        "input": "#F3F4F8",
        "line": "#EDF0F7",
        "success": "#09B42C",
        "success_bg": "#E5F7E9",
        "warning": "#FF8719",
        "warning_bg": "#FFF3E6",
        "wait": "#808080",
        "wait_bg": "#F0F1F5",
        "error": "#FA5151",
    }
    FONT = "Noto Sans SC"

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("廾匸转换")
        self.root.overrideredirect(True)
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
        self.drag_origin: tuple[int, int] | None = None
        self.canvas = tk.Canvas(self.root, background=self.COLORS["page"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.output_entry = self._entry(self.output)
        self.tags_entry = self._entry(self.tags)
        self.vault_entry = self._entry(self.vault_root)
        self.canvas.bind("<Configure>", lambda _event: self._draw())
        self.canvas.bind("<Button-1>", self._click)
        self.canvas.bind("<Motion>", self._hover)
        self.canvas.bind("<ButtonPress-1>", self._drag_start, add="+")
        self.canvas.bind("<B1-Motion>", self._drag_move)
        self.root.bind("<Escape>", lambda _event: self.root.destroy())
        self._draw()
        self.root.after(100, self._poll_events)

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

    def _round(self, x1: int, y1: int, x2: int, y2: int, radius: int, fill: str) -> None:
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
            outline="",
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
        fill = (
            self.COLORS["primary"]
            if primary
            else self.COLORS["quiet"]
            if quiet
            else self.COLORS["secondary"]
        )
        if not enabled:
            fill, color = self.COLORS["line"], self.COLORS["muted"]
        else:
            color = (
                "#FFFFFF" if primary else self.COLORS["body"] if quiet else self.COLORS["primary"]
            )
        self._round(x, y, x + width, y + 36, 8, fill)
        self.canvas.create_text(
            x + width // 2,
            y + 18,
            text=text,
            fill=color,
            font=(self.FONT, 12, "bold" if not quiet else "normal"),
        )
        if enabled:
            self.hitboxes.append((key, (x, y, x + width, y + 36)))

    def _check(
        self, key: str, x: int, y: int, variable: tk.BooleanVar, label: str, enabled: bool = True
    ) -> None:
        self._round(
            x,
            y,
            x + 16,
            y + 16,
            4,
            self.COLORS["primary"] if variable.get() else self.COLORS["line"],
        )
        if not variable.get():
            self._round(x, y, x + 16, y + 16, 4, self.COLORS["muted"])
            self._round(x + 1, y + 1, x + 15, y + 15, 3, self.COLORS["line"])
        if variable.get():
            self.canvas.create_text(
                x + 8, y + 8, text="✓", fill="#FFFFFF", font=("Segoe UI", 11, "bold")
            )
        self._text(
            x + 25, y + 8, label, color=self.COLORS["body"] if enabled else self.COLORS["muted"]
        )
        if enabled:
            self.hitboxes.append((key, (x, y - 4, x + 210, y + 20)))

    def _pill(self, x: int, y: int, text: str, color: str, background: str) -> None:
        width = len(text) * 12 + 24
        self._round(x, y, x + width, y + 30, 15, background)
        self.canvas.create_text(
            x + width // 2, y + 15, text=text, fill=color, font=(self.FONT, 11, "bold")
        )

    def _draw_title_bar(self, width: int) -> None:
        self._round(0, 0, width, 40, 0, "#FFFFFF")
        self._round(18, 9, 40, 31, 6, self.COLORS["primary"])
        self.canvas.create_text(29, 20, text="廾", fill="#FFFFFF", font=(self.FONT, 14, "bold"))
        self._text(50, 20, "廾匸转换", 12, self.COLORS["text"], True)
        for index, (key, glyph) in enumerate(
            (("minimize", "−"), ("maximize", "□"), ("close", "×"))
        ):
            x = width - 102 + index * 34
            self.canvas.create_text(x + 17, 20, text=glyph, fill="#999999", font=("Segoe UI", 15))
            self.hitboxes.append((key, (x, 0, x + 34, 40)))

    def _card(self, x: int, y: int, width: int, height: int, title: str) -> None:
        self._round(x, y, x + width, y + height, 12, self.COLORS["card"])
        self._text(x + 20, y + 25, title, 16, self.COLORS["text"], True)

    def _draw(self) -> None:
        self.canvas.delete("all")
        self._sync_option_states()
        width, height = max(1040, self.root.winfo_width()), max(760, self.root.winfo_height())
        self.hitboxes.clear()
        self._draw_title_bar(width)
        margin, card_width = 16, width - 32
        self._text(margin, 74, "廾匸转换", 22, self.COLORS["text"], True)
        self._text(margin, 102, "Office 文件转 Markdown", 13, self.COLORS["muted"])
        self._pill(
            width - 218,
            72,
            "本地处理 · 不上传文件",
            self.COLORS["primary"],
            self.COLORS["secondary"],
        )
        self._draw_import(margin, 126, card_width, width)
        rules_height = 208
        self._draw_rules(margin, 272, card_width, width, rules_height)
        queue_y, queue_h = 494, max(228, height - 572)
        self._card(margin, queue_y, card_width, queue_h, "待处理文件")
        self._draw_queue_header(width, queue_y)
        if self.sources:
            self._draw_real_queue(margin, queue_y)
        else:
            self._draw_empty_queue(width, queue_y)
        action_y = height - 62
        self._button(
            "start", margin + 6, action_y, 138, "开始处理", True, enabled=bool(self.sources)
        )
        self._button(
            "cancel", margin + 158, action_y, 122, "取消队列", quiet=True, enabled=bool(self.worker)
        )
        selected = self._selected_result()
        can_open = bool(selected and selected.result)
        self._button("report", width - 272, action_y, 120, "打开选中报告", enabled=can_open)
        self._button("open", width - 138, action_y, 120, "打开选中输出", enabled=can_open)
        self.canvas.create_text(
            width // 2,
            height - 18,
            text=self.status.get(),
            fill=self.COLORS["muted"],
            font=(self.FONT, 12),
        )

    def _sync_option_states(self) -> None:
        state = "normal" if self.obsidian.get() else "disabled"
        self.tags_entry.configure(state=state)
        self.vault_entry.configure(state=state)

    def _draw_import(self, x: int, y: int, width: int, page_width: int) -> None:
        self._card(x, y, width, 132, "导入文件")
        self._text(
            x + 20,
            y + 62,
            "选择需要归档的 Word、PowerPoint 或 Excel 文件。可重复添加，按队列顺序处理。",
        )
        self._button("files", x + 20, y + 86, 126, "选择文件", True)
        self._button("folder", x + 162, y + 86, 144, "扫描文件夹")
        self._check("recursive", page_width - 160, y + 100, self.recursive, "包含子文件夹")

    def _draw_rules(
        self, x: int, y: int, width: int, page_width: int, height: int
    ) -> None:
        self._card(x, y, width, height, "输出规则")
        label_x, entry_x, entry_w = x + 20, x + 106, max(360, page_width - 390)
        self._text(label_x, y + 75, "保存到", 13, self.COLORS["body"], True)
        self._round(entry_x, y + 56, entry_x + entry_w, y + 92, 8, self.COLORS["input"])
        self.canvas.create_window(
            entry_x + 12,
            y + 74,
            window=self.output_entry,
            anchor="w",
            width=entry_w - 24,
            height=30,
        )
        self._button("output", entry_x + entry_w + 12, y + 56, 112, "选择位置")
        self._button("default", entry_x + entry_w + 136, y + 56, 112, "设为默认", quiet=True)
        self.canvas.create_line(
            label_x, y + 112, page_width - 36, y + 112, fill=self.COLORS["line"]
        )
        options_y = y + 124
        self._check("obsidian", label_x, options_y, self.obsidian, "Obsidian 模式")
        self._text(label_x + 150, options_y + 8, "标签（默认值）", 12, self.COLORS["muted"])
        if self.obsidian.get():
            self._round(
                label_x + 316, options_y - 9, label_x + 496, options_y + 27, 8, self.COLORS["input"]
            )
            self.canvas.create_window(
                label_x + 326,
                options_y + 9,
                window=self.tags_entry,
                anchor="w",
                width=160,
                height=30,
            )
        else:
            self._text(label_x + 316, options_y + 8, "启用后可设置", 12, self.COLORS["muted"])
        right_x = page_width // 2 + 10
        self._check(
            "source-link",
            right_x,
            options_y,
            self.include_source_link,
            "添加原文件链接",
            self.obsidian.get(),
        )
        vault_x, vault_w = right_x + 138, max(180, page_width - right_x - 282)
        if self.obsidian.get():
            self._round(
                vault_x, options_y - 9, vault_x + vault_w, options_y + 27, 8, self.COLORS["input"]
            )
            self.canvas.create_window(
                vault_x + 10, options_y + 9,
                window=self.vault_entry,
                anchor="w",
                width=vault_w - 20,
                height=30,
            )
        self._button(
            "vault",
            vault_x + vault_w + 12,
            options_y - 9,
            112,
            "选择 Vault",
            enabled=self.obsidian.get(),
        )
        visual_y = y + 168
        self._check(
            "copy", label_x, visual_y, self.copy_source, "复制原文件到输出目录", self.obsidian.get()
        )
        self._text(label_x + 214, visual_y + 8, "PPTX 视觉附件", 13, self.COLORS["body"], True)
        self._check("png", label_x + 342, visual_y, self.export_pptx_png, "导出每页 PNG")
        self._text(
            label_x + 490, visual_y + 8, "WPS 演示优先 · PowerPoint 后备", 12, self.COLORS["muted"]
        )
        self._check(
            "pdf",
            page_width - 180,
            visual_y,
            self.export_pptx_pdf,
            "导出版式 PDF",
        )

    def _draw_queue_header(self, width: int, y: int) -> None:
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
        self._text(width - 36, y + 25, meta, 12, self.COLORS["muted"], anchor="e")
        self._round(36, y + 54, width - 36, y + 64, 5, self.COLORS["line"])
        if progress:
            self._round(
                36, y + 54, int(36 + (width - 72) * progress), y + 64, 5, self.COLORS["primary"]
            )

    def _draw_empty_queue(self, width: int, y: int) -> None:
        self.canvas.create_text(
            width // 2,
            y + 116,
            text="选择文件或扫描文件夹后，文件会按添加顺序显示在这里。",
            fill=self.COLORS["muted"],
            font=(self.FONT, 13),
        )

    def _draw_real_queue(self, x: int, y: int) -> None:
        mapping = {
            BatchStatus.RUNNING: ("转换中", self.COLORS["primary"], self.COLORS["secondary"]),
            BatchStatus.SUCCESS: ("已完成", self.COLORS["success"], self.COLORS["success_bg"]),
            BatchStatus.WARNING: ("有警告", self.COLORS["warning"], self.COLORS["warning_bg"]),
            BatchStatus.FAILED: ("转换失败", self.COLORS["error"], "#FFE8E8"),
            BatchStatus.CANCELLED: ("已取消", self.COLORS["wait"], self.COLORS["wait_bg"]),
        }
        for index, source in enumerate(self.sources):
            item = self.results.get(str(source))
            state, color, background = (
                mapping.get(item.status, ("等待中", self.COLORS["wait"], self.COLORS["wait_bg"]))
                if item
                else ("等待中", self.COLORS["wait"], self.COLORS["wait_bg"])
            )
            detail = (
                item.error_message if item and item.error_message else self._source_detail(source)
            )
            badge, badge_color = self._file_badge(source)
            self._draw_file_row(
                x + 20,
                y + 82 + index * 34,
                badge,
                badge_color,
                source.name,
                detail,
                state,
                color,
                background,
                str(source),
            )

    def _draw_file_row(
        self,
        x: int,
        y: int,
        badge: str,
        badge_color: str,
        name: str,
        detail: str,
        state: str,
        color: str,
        background: str,
        key: str | None = None,
    ) -> None:
        self._round(x, y, x + 30, y + 30, 8, badge_color)
        self.canvas.create_text(
            x + 15, y + 15, text=badge, fill="#FFFFFF", font=(self.FONT, 12, "bold")
        )
        self._text(x + 44, y + 9, name, 13, self.COLORS["text"], True)
        self._text(x + 44, y + 24, detail, 12, self.COLORS["muted"])
        width = self.root.winfo_width()
        if state == "progress":
            self._round(width - 214, y + 12, width - 94, y + 18, 3, self.COLORS["line"])
            self._round(width - 214, y + 12, width - 132, y + 18, 3, self.COLORS["primary"])
            self._text(width - 78, y + 15, "68%", 12, self.COLORS["primary"])
        else:
            pill_width = max(72, len(state) * 12 + 24)
            self._round(width - 36 - pill_width, y + 1, width - 36, y + 31, 15, background)
            self.canvas.create_text(
                width - 36 - pill_width // 2,
                y + 16,
                text=state,
                fill=color,
                font=(self.FONT, 11, "bold"),
            )
        if key:
            self.hitboxes.append((f"select:{key}", (x, y, width - 30, y + 32)))

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
        kind = {".docx": "Word 文档", ".pptx": "PowerPoint 演示", ".xlsx": "Excel 表格"}.get(
            source.suffix.lower(), "Office 文件"
        )
        return f"{size} · {kind}"

    def _click(self, event: tk.Event[tk.Misc]) -> None:
        for key, (x1, y1, x2, y2) in reversed(self.hitboxes):
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self._dispatch(key)
                return

    def _hover(self, event: tk.Event[tk.Misc]) -> None:
        self.canvas.configure(
            cursor="hand2"
            if any(
                x1 <= event.x <= x2 and y1 <= event.y <= y2
                for _key, (x1, y1, x2, y2) in self.hitboxes
            )
            else ""
        )

    def _drag_start(self, event: tk.Event[tk.Misc]) -> None:
        self.drag_origin = (event.x_root, event.y_root) if event.y <= 40 else None

    def _drag_move(self, event: tk.Event[tk.Misc]) -> None:
        if self.drag_origin:
            dx, dy = event.x_root - self.drag_origin[0], event.y_root - self.drag_origin[1]
            self.root.geometry(f"+{self.root.winfo_x() + dx}+{self.root.winfo_y() + dy}")
            self.drag_origin = (event.x_root, event.y_root)

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
        elif key == "minimize":
            self.root.iconify()
        elif key == "maximize":
            self.root.state("zoomed" if self.root.state() != "zoomed" else "normal")
        elif key == "close":
            self.root.destroy()
        elif key.startswith("select:"):
            self.selected_key = key.removeprefix("select:")
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

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    MainWindow().run()
