from __future__ import annotations

from pathlib import Path

from .models import Block, ConversionOptions, ParsedDocument, WarningItem
from .security import safe_name


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>").strip()


def render_blocks(blocks: list[Block], asset_prefix: str = "assets") -> str:
    lines: list[str] = []
    for block in blocks:
        if block.kind == "heading":
            lines.extend(["#" * max(1, min(6, block.level or 1)) + " " + block.text.strip(), ""])
        elif block.kind == "slide":
            lines.extend([f"## 第 {block.text} 页", ""])
        elif block.kind == "page":
            lines.extend([f"## 第 {block.text} 页", ""])
        elif block.kind == "paragraph":
            lines.extend([block.text.strip(), ""])
        elif block.kind == "quote":
            lines.extend([f"> {block.text.strip()}", ""])
        elif block.kind == "list":
            indent = "  " * max(0, block.level)
            lines.append(f"{indent}- {block.text.strip()}")
        elif block.kind == "table" and block.rows:
            header = [_escape(cell) for cell in block.rows[0]]
            lines.append("| " + " | ".join(header) + " |")
            lines.append("| " + " | ".join(["---"] * len(header)) + " |")
            for row in block.rows[1:]:
                padded = row + [""] * max(0, len(header) - len(row))
                lines.append(
                    "| " + " | ".join(_escape(cell) for cell in padded[: len(header)]) + " |"
                )
            lines.append("")
        elif block.kind == "image" and block.asset_name:
            lines.extend(
                [f"![{block.text or block.asset_name}]({asset_prefix}/{block.asset_name})", ""]
            )
        elif block.kind == "link":
            lines.extend([f"[{block.text}]({block.text})", ""])
    return "\n".join(lines).strip() + "\n"


def render_frontmatter(
    source: Path, document: ParsedDocument, options: ConversionOptions, source_link: str | None
) -> list[str]:
    if not (options.obsidian_mode or options.include_frontmatter):
        return []
    lines = [
        "---",
        f'source_file: "{source.name.replace(chr(34), chr(39))}"',
        f"source_format: {document.format}",
        'converter: "廾匸转换"',
    ]
    if document.warnings:
        lines.append("warnings:")
        lines.extend(f"  - {code}" for code in warning_codes(document.warnings))
    if options.tags:
        lines.append("tags:")
        lines.extend(f"  - {tag}" for tag in options.tags)
    if source_link:
        lines.append(f'source_link: "{source_link}"')
    return lines + ["---", ""]


def render_index(
    document: ParsedDocument,
    source: Path | None = None,
    options: ConversionOptions | None = None,
    source_link: str | None = None,
    has_pptx_png: bool = False,
    has_pptx_pdf: bool = False,
) -> str:
    lines = render_frontmatter(source, document, options, source_link) if source and options else []
    output_name = safe_name(source.stem if source else document.title)
    lines.extend([f"# {document.title}", "", f"源文件格式：`{document.format.upper()}`", ""])
    if document.format == "xlsx":
        lines.extend([f"- [转换内容](markdown/{output_name}.md)", "", "## 工作表", ""])
        for sheet_name in document.sheets:
            lines.append(f"- [{sheet_name}](markdown/sheets/{safe_name(sheet_name)}.md)")
    else:
        lines.append(f"- [转换内容](markdown/{output_name}.md)")
    lines.extend(["", f"- [转换报告](reports/{output_name}转换报告.md)"])
    if document.format == "pptx" and has_pptx_png:
        lines.append("- [每页预览图](visuals/pages/)")
    if document.format == "pptx" and has_pptx_pdf:
        lines.append(f"- [版式 PDF](visuals/{output_name}.pdf)")
    if source_link:
        lines.append(f"- [原文件]({source_link})")
    lines.append("")
    return "\n".join(lines)


def render_workbook_entry(document: ParsedDocument) -> str:
    lines = [f"# {document.title}", "", "## 工作表", ""]
    for sheet_name in document.sheets:
        lines.append(f"- [{sheet_name}](sheets/{safe_name(sheet_name)}.md)")
    return "\n".join(lines) + "\n"


def render_report(document: ParsedDocument) -> str:
    lines = [
        "# 转换报告",
        "",
        f"- 源文件格式：`{document.format.upper()}`",
        f"- 导出资源数量：{len(document.assets)}",
        "",
    ]
    if document.warnings:
        lines.extend(["## 警告", ""])
        for warning in document.warnings:
            location = f" ({warning.location})" if warning.location else ""
            lines.append(f"- `{warning.code}`{location}: {warning.message}")
    else:
        lines.extend(["## 警告", "", "本次转换未产生警告。"])
    return "\n".join(lines) + "\n"


def warning_codes(warnings: list[WarningItem]) -> list[str]:
    return sorted({warning.code for warning in warnings})
