from __future__ import annotations

from dataclasses import dataclass
from tkinter import ttk


@dataclass(frozen=True)
class Theme:
    page: str = "#EFF1F5"
    surface: str = "#FFFFFF"
    primary: str = "#3660F4"
    primary_active: str = "#2952D6"
    text: str = "#181818"
    body: str = "#4D4D4D"
    muted: str = "#808080"
    line: str = "#D8DEEA"
    success: str = "#098C28"
    warning: str = "#B95C00"
    error: str = "#C92D2D"
    spacing: int = 12
    control_height: int = 34


TOKENS = Theme()


def apply_theme(root) -> ttk.Style:
    style = ttk.Style(root)
    style.configure("App.TFrame", background=TOKENS.page)
    style.configure("Panel.TFrame", background=TOKENS.surface)
    style.configure(
        "Title.TLabel",
        background=TOKENS.page,
        foreground=TOKENS.text,
        font=("Segoe UI", 16, "bold"),
    )
    style.configure(
        "Heading.TLabel",
        background=TOKENS.surface,
        foreground=TOKENS.text,
        font=("Segoe UI", 11, "bold"),
    )
    style.configure(
        "Body.TLabel", background=TOKENS.surface, foreground=TOKENS.body, font=("Segoe UI", 9)
    )
    style.configure(
        "Muted.TLabel", background=TOKENS.surface, foreground=TOKENS.muted, font=("Segoe UI", 9)
    )
    style.configure("Primary.TButton", padding=(12, 6))
    style.configure("Secondary.TButton", padding=(10, 6))
    style.configure("Treeview", rowheight=30, font=("Segoe UI", 9))
    style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
    return style
