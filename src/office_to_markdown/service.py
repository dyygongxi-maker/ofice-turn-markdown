from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from .adapters import parse_source
from .markdown import render_blocks, render_index, render_report, warning_codes
from .models import ConversionResult
from .security import ValidationError, ensure_output_parent, safe_name, validate_input


class ConversionService:
    def convert(self, source: Path, output_parent: Path) -> ConversionResult:
        validate_input(source)
        ensure_output_parent(output_parent)
        document = parse_source(source)
        final_path = output_parent / f"{safe_name(source.stem)}-markdown"
        if final_path.exists():
            raise ValidationError(
                "输出目录已存在。请选择其他输出目录，或重命名源文件后再试。"
            )
        staging = Path(tempfile.mkdtemp(prefix=f".{safe_name(source.stem)}-", dir=output_parent))
        try:
            (staging / "assets").mkdir()
            for asset in document.assets:
                (staging / "assets" / asset.name).write_bytes(asset.data)
            (staging / "index.md").write_text(render_index(document), encoding="utf-8")
            if document.format == "xlsx":
                sheets = staging / "sheets"
                sheets.mkdir()
                for name, blocks in document.sheets.items():
                    (sheets / f"{safe_name(name)}.md").write_text(
                        render_blocks(blocks, "../assets"), encoding="utf-8"
                    )
            else:
                name = "content.md" if document.format == "docx" else "slides.md"
                (staging / name).write_text(render_blocks(document.blocks), encoding="utf-8")
            report_path = staging / "conversion-report.md"
            report_path.write_text(render_report(document), encoding="utf-8")
            manifest = {
                "source_name": source.name,
                "source_format": document.format,
                "warning_codes": warning_codes(document.warnings),
                "asset_count": len(document.assets),
            }
            (staging / "source-manifest.json").write_text(
                json.dumps(manifest, indent=2), encoding="utf-8"
            )
            staging.rename(final_path)
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise
        return ConversionResult(
            final_path, final_path / "conversion-report.md", tuple(document.warnings)
        )
