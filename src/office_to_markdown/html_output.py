from __future__ import annotations

from html import escape

from .models import Block, ParsedDocument


def _text(value: str) -> str:
    return escape(value, quote=True).replace("\n", "<br>\n")


def _render_block(block: Block) -> str:
    if block.kind == "heading":
        level = max(1, min(6, block.level or 1))
        return f"<h{level}>{_text(block.text)}</h{level}>"
    if block.kind in {"slide", "page"}:
        return f"<h2>第 {_text(block.text)} 页</h2>"
    if block.kind == "paragraph":
        return f"<p>{_text(block.text)}</p>"
    if block.kind == "quote":
        return f"<blockquote>{_text(block.text)}</blockquote>"
    if block.kind == "list":
        return f"<ul><li>{_text(block.text)}</li></ul>"
    if block.kind == "table" and block.rows:
        header = "".join(f"<th>{_text(cell)}</th>" for cell in block.rows[0])
        body = "".join(
            "<tr>" + "".join(f"<td>{_text(cell)}</td>" for cell in row) + "</tr>"
            for row in block.rows[1:]
        )
        return f"<table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table>"
    if block.kind == "link" and block.text.startswith(("https://", "http://")):
        url = escape(block.text, quote=True)
        return f'<p><a href="{url}" rel="noreferrer noopener" target="_blank">{url}</a></p>'
    return ""


def render_html(document: ParsedDocument) -> str:
    blocks = list(document.blocks)
    for sheet_name, sheet_blocks in document.sheets.items():
        blocks.append(Block("heading", sheet_name, 1))
        starts_with_heading = bool(sheet_blocks) and sheet_blocks[0].kind == "heading"
        sheet_content = sheet_blocks[1:] if starts_with_heading else sheet_blocks
        blocks.extend(sheet_content)
    body = "\n".join(filter(None, (_render_block(block) for block in blocks)))
    title = escape(document.title, quote=True)
    return (
        "<!doctype html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        f"<title>{title}</title>\n"
        "<style>body{max-width:960px;margin:40px auto;padding:0 24px;"
        "font:16px/1.6 sans-serif;color:#181818}"
        "table{border-collapse:collapse;width:100%;margin:16px 0}"
        "th,td{border:1px solid #ddd;padding:8px;text-align:left}"
        "th{background:#f3f4f8}blockquote{border-left:4px solid #3660F4;"
        "margin:16px 0;padding-left:16px;color:#4D4D4D}</style>\n"
        "</head>\n<body>\n"
        f"{body}\n"
        "</body>\n</html>\n"
    )
