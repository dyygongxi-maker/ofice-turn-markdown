from __future__ import annotations

# ruff: noqa: E501
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from .state import UiPhase, UiState


class StatusBar(ttk.Frame):
    def __init__(
        self, master: tk.Misc, state: UiState, start: Callable[[], None], cancel: Callable[[], None]
    ) -> None:
        super().__init__(master, style="Panel.TFrame", padding=(16, 10))
        self.state = state
        self.columnconfigure(0, weight=1)
        ttk.Label(self, textvariable=state.status, style="Body.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.cancel_button = ttk.Button(self, text="取消队列", command=cancel)
        self.cancel_button.grid(row=0, column=1, padx=(8, 0))
        self.start_button = ttk.Button(
            self, text="开始转换", command=start, style="Primary.TButton"
        )
        self.start_button.grid(row=0, column=2, padx=(8, 0))
        self.refresh()

    def refresh(self) -> None:
        self.start_button.state(("!disabled" if self.state.can_start else "disabled",))
        self.cancel_button.state(("!disabled" if self.state.can_cancel else "disabled",))
        if self.state.phase is UiPhase.CANCELLING:
            self.cancel_button.configure(text="正在取消")
        else:
            self.cancel_button.configure(text="取消队列")
