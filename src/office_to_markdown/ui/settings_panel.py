from __future__ import annotations

# ruff: noqa: E501
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from .state import UiState


class SettingsPanel(ttk.Frame):
    """Output and archive controls bound to a shared UI state object."""

    def __init__(
        self,
        master: tk.Misc,
        state: UiState,
        choose_output: Callable[[], None],
        save_default: Callable[[], None],
        choose_vault: Callable[[], None],
    ) -> None:
        super().__init__(master, style="Panel.TFrame", padding=16)
        self.state = state
        self._choose_output = choose_output
        self._save_default = save_default
        self._choose_vault = choose_vault
        self._obsidian_controls: list[ttk.Widget] = []
        self.columnconfigure(0, weight=1)
        self._build()
        state.obsidian.trace_add("write", self._sync_option_state)
        self._sync_option_state()

    def _build(self) -> None:
        ttk.Label(self, text="转换设置", style="Heading.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(self, text="输出位置", style="Body.TLabel").grid(
            row=1, column=0, sticky="w", pady=(16, 4)
        )
        output = ttk.Frame(self, style="Panel.TFrame")
        output.grid(row=2, column=0, sticky="ew")
        output.columnconfigure(0, weight=1)
        ttk.Entry(output, textvariable=self.state.output).grid(row=0, column=0, sticky="ew")
        ttk.Button(
            output, text="浏览", command=self._choose_output, style="Secondary.TButton"
        ).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(
            self, text="设为默认", command=self._save_default, style="Secondary.TButton"
        ).grid(row=3, column=0, sticky="w", pady=(8, 16))

        ttk.Separator(self).grid(row=4, column=0, sticky="ew")
        check = ttk.Checkbutton(self, text="启用 Obsidian 归档", variable=self.state.obsidian)
        check.grid(row=5, column=0, sticky="w", pady=(16, 8))
        self._obsidian_controls.append(check)

        ttk.Label(self, text="标签（逗号分隔）", style="Body.TLabel").grid(
            row=6, column=0, sticky="w", pady=(0, 4)
        )
        tags = ttk.Entry(self, textvariable=self.state.tags)
        tags.grid(row=7, column=0, sticky="ew")
        self._obsidian_controls.append(tags)

        ttk.Label(self, text="Vault 根目录", style="Body.TLabel").grid(
            row=8, column=0, sticky="w", pady=(10, 4)
        )
        vault = ttk.Frame(self, style="Panel.TFrame")
        vault.grid(row=9, column=0, sticky="ew")
        vault.columnconfigure(0, weight=1)
        vault_entry = ttk.Entry(vault, textvariable=self.state.vault_root)
        vault_entry.grid(row=0, column=0, sticky="ew")
        vault_button = ttk.Button(vault, text="选择 Vault", command=self._choose_vault)
        vault_button.grid(row=0, column=1, padx=(8, 0))
        self._obsidian_controls.extend((vault_entry, vault_button))
        for row, text, variable in (
            (10, "添加原文件链接", self.state.include_source_link),
            (11, "复制原文件到输出目录", self.state.copy_source),
        ):
            control = ttk.Checkbutton(self, text=text, variable=variable)
            control.grid(row=row, column=0, sticky="w", pady=(8, 0))
            self._obsidian_controls.append(control)

        ttk.Separator(self).grid(row=12, column=0, sticky="ew", pady=(16, 0))
        ttk.Label(self, text="PPTX 视觉附件", style="Heading.TLabel").grid(
            row=13, column=0, sticky="w", pady=(16, 4)
        )
        ttk.Checkbutton(self, text="导出每页 PNG", variable=self.state.export_pptx_png).grid(
            row=14, column=0, sticky="w"
        )
        ttk.Label(self, text="WPS 演示优先，PowerPoint 后备", style="Muted.TLabel").grid(
            row=15, column=0, sticky="w", padx=(24, 0), pady=(0, 6)
        )
        ttk.Checkbutton(self, text="导出版式 PDF", variable=self.state.export_pptx_pdf).grid(
            row=16, column=0, sticky="w"
        )

    def set_editable(self, editable: bool) -> None:
        state = "!disabled" if editable else "disabled"
        for child in self.winfo_children():
            self._set_widget_state(child, state)
        self._sync_option_state()

    def _set_widget_state(self, widget: tk.Misc, state: str) -> None:
        if isinstance(widget, ttk.Widget):
            widget.state((state,))
        for child in widget.winfo_children():
            self._set_widget_state(child, state)

    def _sync_option_state(self, *_args: object) -> None:
        enabled = self.state.obsidian.get() and self.state.can_edit
        for control in self._obsidian_controls[1:]:
            control.state(("!disabled" if enabled else "disabled",))
