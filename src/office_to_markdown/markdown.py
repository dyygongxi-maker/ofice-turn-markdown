from __future__ import annotations

from .models import Block, ParsedDocument, WarningItem
from .security import safe_name


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>").strip()


def render_blocks(blocks: list[Block], asset_prefix: str = "assets") -> str:
    lines: list[str] = []
    for block in blocks:
        if block.kind == "heading":
            lines.extend(["#" * max(1, min(6, block.level or 1)) + " " + block.text.strip(), ""])
        elif block.kind == "slide":
            lines.extend([f"## Slide {block.text}", ""])
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
    return "\n".join(lines).strip() + "\n"


def render_index(document: ParsedDocument) -> str:
    lines = [f"# {document.title}", "", f"Source format: `{document.format.upper()}`", ""]
    if document.format == "xlsx":
        lines.extend(["## Sheets", ""])
        for sheet_name in document.sheets:
            lines.append(f"- [{sheet_name}](sheets/{safe_name(sheet_name)}.md)")
    else:
        content = "content.md" if document.format == "docx" else "slides.md"
        lines.append(f"- [Converted content]({content})")
    lines.extend(["", "- [Conversion report](conversion-report.md)", ""])
    return "\n".join(lines)


def render_report(document: ParsedDocument) -> str:
    lines = [
        "# Conversion report",
        "",
        f"- Source format: `{document.format.upper()}`",
        f"- Exported assets: {len(document.assets)}",
        "",
    ]
    if document.warnings:
        lines.extend(["## Warnings", ""])
        for warning in document.warnings:
            location = f" ({warning.location})" if warning.location else ""
            lines.append(f"- `{warning.code}`{location}: {warning.message}")
    else:
        lines.extend(["## Warnings", "", "No conversion warnings were emitted."])
    return "\n".join(lines) + "\n"


def warning_codes(warnings: list[WarningItem]) -> list[str]:
    return sorted({warning.code for warning in warnings})
