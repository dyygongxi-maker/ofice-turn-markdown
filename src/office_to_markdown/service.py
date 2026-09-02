from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

from .adapters import parse_source
from .markdown import (
    render_blocks,
    render_index,
    render_report,
    render_workbook_entry,
    warning_codes,
)
from .models import ConversionOptions, ConversionResult, WarningItem
from .security import (
    ValidationError,
    ensure_output_parent,
    relative_source_path,
    safe_name,
    validate_input,
    validate_tags,
)
from .visuals import PptxVisualExporter, VisualExportError


class ConversionService:
    def __init__(self, visual_exporter: PptxVisualExporter | None = None) -> None:
        self.visual_exporter = visual_exporter or PptxVisualExporter()

    def convert(
        self, source: Path, output_parent: Path, options: ConversionOptions | None = None
    ) -> ConversionResult:
        options = options or ConversionOptions()
        validate_input(source)
        ensure_output_parent(output_parent)
        validate_tags(options.tags)
        if options.copy_source and not options.obsidian_mode:
            raise ValidationError("复制原文件仅可在 Obsidian 模式中启用。")
        source_link = None
        if options.include_source_link:
            if options.source_link_root is None:
                raise ValidationError("请指定 Obsidian 归档根目录以生成原文件链接。")
            relative_source_path(source, options.source_link_root)
        document = parse_source(source)
        final_path = output_parent / f"{safe_name(source.stem)}-markdown"
        if final_path.exists():
            raise ValidationError("输出目录已存在。请选择其他输出目录，或重命名源文件后再试。")
        staging = Path(tempfile.mkdtemp(prefix=f".{safe_name(source.stem)}-", dir=output_parent))
        try:
            if options.include_source_link:
                source_link = Path(os.path.relpath(source, final_path)).as_posix()
            (staging / "assets").mkdir()
            markdown_dir = staging / "markdown"
            markdown_dir.mkdir()
            reports_dir = staging / "reports"
            reports_dir.mkdir()
            output_name = safe_name(source.stem)
            has_pptx_png = False
            has_pptx_pdf = False
            for asset in document.assets:
                (staging / "assets" / asset.name).write_bytes(asset.data)
            if document.format == "pptx" and (options.export_pptx_png or options.export_pptx_pdf):
                visuals_dir = staging / "visuals"
                try:
                    self.visual_exporter.export(
                        source,
                        visuals_dir,
                        options.export_pptx_png,
                        options.export_pptx_pdf,
                    )
                    has_pptx_png = options.export_pptx_png
                    has_pptx_pdf = options.export_pptx_pdf
                except VisualExportError:
                    shutil.rmtree(visuals_dir, ignore_errors=True)
                    document.warnings.append(
                        WarningItem(
                            "PPTX_VISUAL_EXPORT_FAILED",
                            "PPT 视觉预览未导出，请确认本机 Microsoft PowerPoint 可用。",
                        )
                    )
            (staging / "index.md").write_text(
                render_index(
                    document,
                    source,
                    options,
                    source_link,
                    has_pptx_png,
                    has_pptx_pdf,
                ),
                encoding="utf-8",
            )
            if document.format == "xlsx":
                sheets = markdown_dir / "sheets"
                sheets.mkdir()
                for name, blocks in document.sheets.items():
                    (sheets / f"{safe_name(name)}.md").write_text(
                        render_blocks(blocks, "../../assets"), encoding="utf-8"
                    )
                (markdown_dir / f"{output_name}.md").write_text(
                    render_workbook_entry(document), encoding="utf-8"
                )
            else:
                (markdown_dir / f"{output_name}.md").write_text(
                    render_blocks(document.blocks, "../assets"), encoding="utf-8"
                )
            report_path = reports_dir / f"{output_name}转换报告.md"
            report_path.write_text(render_report(document), encoding="utf-8")
            if options.copy_source:
                originals = staging / "originals"
                originals.mkdir()
                shutil.copy2(source, originals / source.name)
            manifest = {
                "source_name": source.name,
                "source_format": document.format,
                "warning_codes": warning_codes(document.warnings),
                "asset_count": len(document.assets),
                "obsidian_mode": options.obsidian_mode,
            }
            (staging / "source-manifest.json").write_text(
                json.dumps(manifest, indent=2), encoding="utf-8"
            )
            staging.rename(final_path)
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise
        return ConversionResult(
            final_path, final_path / "reports" / f"{safe_name(source.stem)}转换报告.md",
            tuple(document.warnings),
        )
