from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from office_to_markdown.app import MainWindow
from office_to_markdown.models import BatchItem, BatchStatus, ConversionResult
from office_to_markdown.ui.state import UiPhase


def run() -> None:
    window = MainWindow()
    window.root.withdraw()
    try:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "output"
            output.mkdir()
            source = root / "source.docx"
            assert window.state.recursive.get() is False
            assert window.queue_panel.tree.winfo_exists()
            assert window.settings_panel.winfo_exists()
            assert window.status_bar.winfo_exists()

            window._add_sources((source, source))
            window.state.output.set(str(output))
            window.refresh()
            assert window.sources == [source]
            assert window.status_bar.start_button.instate(("!disabled",))

            window.state.selected_key = str(source)
            result = ConversionResult(output, root / "report.md", ())
            window.results[str(source)] = BatchItem(source, BatchStatus.WARNING, result=result)
            window.refresh()
            assert window.queue_panel.output_button.instate(("!disabled",))
            assert window.queue_panel.report_button.instate(("!disabled",))

            window.worker = object()  # type: ignore[assignment]
            window.state.set_phase(UiPhase.RUNNING)
            window.refresh()
            assert window.status_bar.start_button.instate(("disabled",))
            assert window.status_bar.cancel_button.instate(("!disabled",))
            assert window.queue_panel.tree.winfo_height() > 0
    finally:
        window.root.destroy()


if __name__ == "__main__":
    run()
