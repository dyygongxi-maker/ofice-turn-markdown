from __future__ import annotations

import base64
import shutil
import subprocess
import sys
from pathlib import Path

from .security import safe_name


class VisualExportError(RuntimeError):
    pass


class _PowerShellVisualExporter:
    script_name: str
    engine_name: str

    def _script_path(self) -> Path:
        bundle_dir = getattr(sys, "_MEIPASS", None)
        if bundle_dir:
            return Path(bundle_dir) / "office_to_markdown" / self.script_name
        return Path(__file__).with_name(self.script_name)

    def export(self, source: Path, output_dir: Path, export_png: bool, export_pdf: bool) -> None:
        if not export_png and not export_pdf:
            return
        script = self._script_path()
        if not script.is_file():
            raise VisualExportError(f"{self.engine_name} visual export script is unavailable")
        output_dir.mkdir(parents=True, exist_ok=True)
        command = self._encoded_command(script, source, output_dir, export_png, export_pdf)
        try:
            completed = subprocess.run(
                [
                    "powershell.exe",
                    "-Sta",
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-EncodedCommand",
                    command,
                ],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=180,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise VisualExportError(f"{self.engine_name} visual export could not start") from error
        if completed.returncode != 0:
            raise VisualExportError(f"{self.engine_name} visual export failed")
        if export_png and not any((output_dir / "pages").glob("slide-*.png")):
            raise VisualExportError(f"{self.engine_name} did not export slide images")
        pdf_path = output_dir / f"{safe_name(source.stem)}.pdf"
        if export_pdf and not pdf_path.is_file():
            raise VisualExportError(f"{self.engine_name} did not export a PDF")

    @staticmethod
    def _encoded_command(
        script: Path, source: Path, output_dir: Path, export_png: bool, export_pdf: bool
    ) -> str:
        def quote(value: Path | str) -> str:
            return "'" + str(value).replace("'", "''") + "'"

        command = (
            f"& {quote(script)} -Source {quote(source)} -OutputDirectory {quote(output_dir)} "
            f"-PdfName {quote(safe_name(source.stem) + '.pdf')} "
            f"-ExportPng ${str(export_png).lower()} -ExportPdf ${str(export_pdf).lower()}"
        )
        return base64.b64encode(command.encode("utf-16-le")).decode("ascii")


class WpsVisualExporter(_PowerShellVisualExporter):
    script_name = "export_wps_pptx_visuals.ps1"
    engine_name = "WPS"


class PowerPointVisualExporter(_PowerShellVisualExporter):
    script_name = "export_pptx_visuals.ps1"
    engine_name = "PowerPoint"


class PptxVisualExporter:
    """Export PPTX visuals through WPS first, then PowerPoint as a fallback."""

    def __init__(
        self,
        wps_exporter: WpsVisualExporter | None = None,
        powerpoint_exporter: PowerPointVisualExporter | None = None,
    ) -> None:
        self.wps_exporter = wps_exporter or WpsVisualExporter()
        self.powerpoint_exporter = powerpoint_exporter or PowerPointVisualExporter()

    def export(self, source: Path, output_dir: Path, export_png: bool, export_pdf: bool) -> None:
        if not export_png and not export_pdf:
            return
        try:
            self.wps_exporter.export(source, output_dir, export_png, export_pdf)
            return
        except VisualExportError:
            shutil.rmtree(output_dir, ignore_errors=True)
        try:
            self.powerpoint_exporter.export(source, output_dir, export_png, export_pdf)
        except VisualExportError as powerpoint_error:
            shutil.rmtree(output_dir, ignore_errors=True)
            raise VisualExportError(
                "WPS and PowerPoint visual export both failed"
            ) from powerpoint_error
