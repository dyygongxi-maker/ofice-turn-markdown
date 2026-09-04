"""Backward-compatible desktop application entry point."""

from .ui.main_window import MainWindow


def main() -> None:
    MainWindow().run()
