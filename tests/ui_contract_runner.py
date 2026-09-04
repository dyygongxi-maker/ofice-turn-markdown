from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from office_to_markdown import app
from office_to_markdown.app import MainWindow
from office_to_markdown.models import BatchItem, BatchStatus, ConversionResult


class RecordingThread:
    instances: list[RecordingThread] = []

    def __init__(self, *, target, args, daemon: bool) -> None:
        self.target = target
        self.args = args
        self.daemon = daemon
        self.started = False
        self.instances.append(self)

    def start(self) -> None:
        self.started = True


def reset(window: MainWindow) -> None:
    window.sources.clear()
    window.results.clear()
    window.selected_key = None
    window.worker = None
    window.output.set("")
    window.tags.set("")
    window.vault_root.set("")
    window.recursive.set(False)
    window.obsidian.set(False)
    window.include_source_link.set(False)
    window.copy_source.set(False)
    window.export_pptx_png.set(False)
    window.export_pptx_pdf.set(False)
    window.status.set("尚未添加文件，文件仅在本机处理。")


def run() -> None:
    original_thread = app.threading.Thread
    window = MainWindow()
    window.root.withdraw()
    try:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "output"
            vault = root / "vault"
            output.mkdir()
            vault.mkdir()
            source = root / "source.docx"

            reset(window)
            window.sources = [source]
            window.output.set(str(output))
            window.tags.set("office-import, project-a")
            window.obsidian.set(True)
            window.include_source_link.set(True)
            window.copy_source.set(True)
            window.export_pptx_png.set(True)
            window.export_pptx_pdf.set(True)
            window.vault_root.set(str(vault))
            app.threading.Thread = RecordingThread
            RecordingThread.instances.clear()
            window.start()
            sources, selected_output, options = RecordingThread.instances[-1].args
            assert sources == (source,)
            assert selected_output == output
            assert options.obsidian_mode and options.include_frontmatter
            assert options.tags == ("office-import", "project-a")
            assert options.include_source_link and options.source_link_root == vault
            assert options.copy_source and options.export_pptx_png and options.export_pptx_pdf

            reset(window)
            window.sources = [source]
            window.output.set(str(output))
            window.obsidian.set(True)
            RecordingThread.instances.clear()
            window.start()
            assert RecordingThread.instances[-1].args[2].tags == ("office-import",)

            reset(window)
            first = root / "first.docx"
            second = root / "second.pptx"
            window._add_sources((second, first, second))
            window._add_sources((first,))
            assert window.sources == [second, first]

            window.selected_key = str(source)
            opened: list[Path] = []
            window._open_path = opened.append
            window.results[str(source)] = BatchItem(source, BatchStatus.FAILED)
            window.open_selected_output()
            window.open_selected_report()
            assert opened == []
            result = ConversionResult(output, root / "report.md", ())
            window.results[str(source)] = BatchItem(source, BatchStatus.WARNING, result=result)
            window.open_selected_output()
            window.open_selected_report()
            assert opened == [result.output_path, result.report_path]

            reset(window)
            window._draw()
            assert "start" not in {key for key, _ in window.hitboxes}
            assert "cancel" not in {key for key, _ in window.hitboxes}
            window.sources = [source]
            window.output.set(str(output))
            window._draw()
            assert "start" in {key for key, _ in window.hitboxes}
            window.worker = object()  # type: ignore[assignment]
            window._draw()
            assert "start" not in {key for key, _ in window.hitboxes}
            assert "cancel" in {key for key, _ in window.hitboxes}
    finally:
        app.threading.Thread = original_thread
        window.root.destroy()


if __name__ == "__main__":
    run()
