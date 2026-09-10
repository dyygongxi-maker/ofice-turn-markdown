from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path

from docx import Document
from openpyxl import load_workbook
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pypdf import PdfReader

from .models import Asset, Block, ParsedDocument, WarningItem
from .security import MAX_COMPRESSED_BYTES, ValidationError, safe_name


def unsupported_pptx_shape_types() -> set:
    names = ("CHART", "EMBEDDED_OLE_OBJECT", "LINKED_OLE_OBJECT", "OLE_CONTROL_OBJECT")
    return {value for name in names if (value := getattr(MSO_SHAPE_TYPE, name, None)) is not None}


def _table_rows(table) -> list[list[str]]:
    return [[cell.text.strip() for cell in row.cells] for row in table.rows]


def parse_docx(source: Path) -> ParsedDocument:
    document = Document(source)
    title = source.stem
    blocks: list[Block] = []
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        style = paragraph.style.name.lower() if paragraph.style else ""
        if style.startswith("heading"):
            level = next((int(char) for char in style if char.isdigit()), 1)
            blocks.append(Block("heading", text, level))
            if level == 1 and title == source.stem:
                title = text
        elif "quote" in style:
            blocks.append(Block("quote", text))
        elif "list" in style:
            blocks.append(Block("list", text, 0))
        else:
            blocks.append(Block("paragraph", text))
    for table in document.tables:
        blocks.append(Block("table", rows=_table_rows(table)))
    assets: list[Asset] = []
    for index, shape in enumerate(document.inline_shapes, start=1):
        try:
            image = shape._inline.graphic.graphicData.pic.blipFill.blip.embed
            part = document.part.related_parts[image]
            extension = part.content_type.rsplit("/", 1)[-1].replace("jpeg", "jpg")
            name = f"image-{index}.{safe_name(extension, 'bin')}"
            assets.append(Asset(name, part.blob))
            blocks.append(Block("image", name, asset_name=name))
        except (AttributeError, KeyError):
            continue
    warnings = []
    if document.inline_shapes and not assets:
        warnings.append(WarningItem("DOCX_IMAGE_EXPORT_FAILED", "有一张内嵌图片未能导出。"))
    return ParsedDocument(title, "docx", blocks, assets=assets, warnings=warnings)


def parse_pptx(source: Path) -> ParsedDocument:
    presentation = Presentation(source)
    document = ParsedDocument(source.stem, "pptx")
    for number, slide in enumerate(presentation.slides, start=1):
        document.blocks.append(Block("slide", str(number)))
        shapes = sorted(slide.shapes, key=lambda shape: (shape.top, shape.left, shape.shape_id))
        for shape in shapes:
            if getattr(shape, "has_table", False):
                document.blocks.append(Block("table", rows=_table_rows(shape.table)))
            elif shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                try:
                    image = shape.image
                except (AttributeError, ValueError):
                    document.warnings.append(
                        WarningItem(
                            "PPTX_LINKED_IMAGE_UNSUPPORTED",
                            "链接或无法读取的图片未导出。",
                            f"第 {number} 页",
                        )
                    )
                    continue
                name = (
                    f"slide-{number}-image-{len(document.assets) + 1}.{safe_name(image.ext, 'bin')}"
                )
                document.assets.append(Asset(name, image.blob))
                document.blocks.append(Block("image", name, asset_name=name))
            elif getattr(shape, "has_text_frame", False):
                is_title = bool(getattr(shape, "is_placeholder", False)) and "TITLE" in str(
                    shape.placeholder_format.type
                )
                for paragraph in shape.text_frame.paragraphs:
                    text = paragraph.text.strip()
                    if not text:
                        continue
                    document.blocks.append(
                        Block(
                            "heading" if is_title else "list" if paragraph.level else "paragraph",
                            text,
                            paragraph.level + 1 if is_title else paragraph.level,
                        )
                    )
                    if is_title and number == 1 and document.title == source.stem:
                        document.title = text
            elif shape.shape_type in unsupported_pptx_shape_types():
                document.warnings.append(
                    WarningItem(
                        "PPTX_OBJECT_UNSUPPORTED",
                        "图表或嵌入对象已跳过。",
                        f"第 {number} 页",
                    )
                )
        try:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            if notes:
                document.blocks.extend([Block("heading", "备注", 3), Block("paragraph", notes)])
        except AttributeError:
            pass
    return document


def parse_xlsx(source: Path) -> ParsedDocument:
    workbook = load_workbook(source, data_only=False, read_only=False)
    values = load_workbook(source, data_only=True, read_only=True)
    document = ParsedDocument(source.stem, "xlsx")
    for sheet in workbook.worksheets:
        if sheet.max_row == 1 and sheet.max_column == 1 and sheet.cell(1, 1).value is None:
            continue
        rows: list[list[str]] = []
        has_formula_without_cache = False
        cached_sheet = values[sheet.title]
        for row in sheet.iter_rows():
            values_row: list[str] = []
            for cell in row:
                value = cell.value
                if isinstance(value, str) and value.startswith("="):
                    cached = cached_sheet[cell.coordinate].value
                    has_formula_without_cache |= cached is None
                    values_row.append(value)
                else:
                    values_row.append("" if value is None else str(value))
            rows.append(values_row)
        document.sheets[sheet.title] = [Block("heading", sheet.title, 1), Block("table", rows=rows)]
        if sheet.merged_cells.ranges:
            document.warnings.append(
                WarningItem(
                    "XLSX_MERGED_CELLS_FLATTENED",
                    "合并单元格已按普通单元格导出。",
                    sheet.title,
                )
            )
        if sheet._charts:
            document.warnings.append(
                WarningItem("XLSX_CHART_UNSUPPORTED", "图表未导出。", sheet.title)
            )
        if has_formula_without_cache:
            document.warnings.append(
                WarningItem(
                    "XLSX_FORMULA_CACHE_UNAVAILABLE",
                    "公式没有可用的缓存显示值。",
                    sheet.title,
                )
            )
    values.close()
    workbook.close()
    return document


def _pdf_links(page) -> list[str]:
    links: list[str] = []
    annotations = page.get("/Annots", [])
    for annotation_reference in annotations:
        annotation = annotation_reference.get_object()
        if annotation.get("/Subtype") != "/Link":
            continue
        action = annotation.get("/A")
        if not action or action.get("/S") != "/URI":
            continue
        uri = str(action.get("/URI", "")).strip()
        if uri.startswith(("https://", "http://")) and uri not in links:
            links.append(uri)
    return links


def parse_pdf(source: Path) -> ParsedDocument:
    reader = PdfReader(source)
    title = source.stem
    if reader.metadata and reader.metadata.title:
        title = str(reader.metadata.title).strip() or source.stem
    document = ParsedDocument(title, "pdf")
    if reader.is_encrypted:
        document.warnings.append(
            WarningItem("PDF_ENCRYPTED_UNSUPPORTED", "加密 PDF 无法提取文本。")
        )
        return document
    has_text = False
    for number, page in enumerate(reader.pages, start=1):
        document.blocks.append(Block("page", str(number)))
        text = (page.extract_text() or "").strip()
        if text:
            has_text = True
            for paragraph in text.split("\n\n"):
                normalized = paragraph.strip()
                if normalized:
                    document.blocks.append(Block("paragraph", normalized))
        document.blocks.extend(Block("link", link) for link in _pdf_links(page))
    if not has_text:
        document.warnings.extend(
            (
                WarningItem("PDF_TEXT_UNAVAILABLE", "PDF 未检测到可提取文本。"),
                WarningItem(
                    "PDF_OCR_REQUIRED", "该 PDF 可能是扫描件，请先使用 OCR 生成可搜索文本。"
                ),
            )
        )
    return document


def parse_txt(source: Path) -> ParsedDocument:
    content, fallback_encoding = _read_text(source)
    document = ParsedDocument(source.stem, "txt")
    if fallback_encoding:
        document.warnings.append(
            WarningItem("TXT_ENCODING_FALLBACK", f"TXT 使用 {fallback_encoding.upper()} 解码。")
        )
    for paragraph in content.replace("\r\n", "\n").replace("\r", "\n").split("\n\n"):
        for line in paragraph.split("\n"):
            text = line.strip()
            if not text:
                continue
            if text.startswith("# "):
                document.blocks.append(Block("heading", text[2:], 1))
            elif text.startswith(("- ", "* ", "+ ")):
                document.blocks.append(Block("list", text[2:]))
            else:
                document.blocks.append(Block("paragraph", text))
    return document


def _read_text(source: Path) -> tuple[str, str | None]:
    for encoding in ("utf-8-sig", "utf-16", "gb18030"):
        try:
            content = source.read_text(encoding=encoding)
            return content, encoding if encoding != "utf-8-sig" else None
        except UnicodeDecodeError:
            continue
    raise ValidationError("文本文件编码无法识别。")


def parse_csv(source: Path) -> ParsedDocument:
    content, fallback_encoding = _read_text(source)
    try:
        dialect = csv.Sniffer().sniff(content[:8192], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    try:
        rows = list(csv.reader(io.StringIO(content, newline=""), dialect))
    except csv.Error as error:
        raise ValidationError("CSV 文件无法解析。") from error
    if not rows:
        raise ValidationError("CSV 文件不包含可转换的行。")
    if len(rows) > 100_000 or any(len(row) > 1_000 for row in rows):
        raise ValidationError("CSV 文件行数或列数超过限制。")
    document = ParsedDocument(source.stem, "csv", [Block("table", rows=rows)])
    if fallback_encoding:
        document.warnings.append(
            WarningItem("CSV_ENCODING_FALLBACK", f"CSV 使用 {fallback_encoding.upper()} 解码。")
        )
    return document


def _table_cells(line: str) -> list[str]:
    value = line.strip()
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|"):
        value = value[:-1]
    return [cell.strip().replace("\\|", "|").replace("\\\\", "\\") for cell in value.split("|")]


def _is_table_divider(line: str) -> bool:
    cells = _table_cells(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def parse_markdown(source: Path) -> ParsedDocument:
    content, fallback_encoding = _read_text(source)
    document = ParsedDocument(source.stem, "markdown")
    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    index = 0
    in_frontmatter = False
    while index < len(lines):
        line = lines[index]
        if index == 0 and line.strip() == "---":
            in_frontmatter = True
            index += 1
            continue
        if in_frontmatter:
            if line.strip() == "---":
                in_frontmatter = False
            index += 1
            continue
        if not line.strip():
            index += 1
            continue
        is_table = line.lstrip().startswith("|")
        if is_table and index + 1 < len(lines) and _is_table_divider(lines[index + 1]):
            rows = [_table_cells(line)]
            index += 2
            while index < len(lines) and lines[index].lstrip().startswith("|"):
                rows.append(_table_cells(lines[index]))
                index += 1
            document.blocks.append(Block("table", rows=rows))
            continue
        if page := re.fullmatch(r"## 第 (\d+) 页", line.strip()):
            document.blocks.append(Block("page", page.group(1)))
        elif heading := re.fullmatch(r"(#{1,6})\s+(.+)", line):
            level = len(heading.group(1))
            text = heading.group(2).strip()
            if level == 1 and document.title == source.stem:
                document.title = text
            document.blocks.append(Block("heading", text, level))
        elif line.startswith("> "):
            document.blocks.append(Block("quote", line[2:].strip()))
        elif (item := re.fullmatch(r"(\s*)[-*+]\s+(.+)", line)):
            document.blocks.append(Block("list", item.group(2).strip(), len(item.group(1)) // 2))
        elif (link := re.fullmatch(r"\[([^\]]+)\]\((https?://[^)]+)\)", line.strip())):
            document.blocks.append(Block("link", link.group(2).strip()))
        elif line.lstrip().startswith("![](") or line.lstrip().startswith("!["):
            document.warnings.append(
                WarningItem("MARKDOWN_IMAGE_UNSUPPORTED", "Markdown 图片未导入，已跳过。")
            )
        else:
            document.blocks.append(Block("paragraph", line.strip()))
        index += 1
    if fallback_encoding:
        document.warnings.append(
            WarningItem(
                "MARKDOWN_ENCODING_FALLBACK", f"Markdown 使用 {fallback_encoding.upper()} 解码。"
            )
        )
    return document


def _json_blocks(payload: object) -> list[Block]:
    if not isinstance(payload, list):
        raise ValidationError("JSON 文档的 blocks 字段无效。")
    supported = {
        "heading",
        "paragraph",
        "quote",
        "list",
        "table",
        "slide",
        "page",
        "link",
        "image",
    }
    blocks: list[Block] = []
    for item in payload:
        if not isinstance(item, dict) or not isinstance(item.get("kind"), str):
            raise ValidationError("JSON 文档包含无效块。")
        kind = item["kind"]
        if kind not in supported:
            raise ValidationError("JSON 文档包含不支持的块类型。")
        text = item.get("text", "")
        level = item.get("level", 0)
        rows = item.get("rows", [])
        asset_name = item.get("asset_name")
        if not isinstance(text, str) or not isinstance(level, int) or isinstance(level, bool):
            raise ValidationError("JSON 文档块字段无效。")
        if asset_name is not None and (
            not isinstance(asset_name, str) or not asset_name or safe_name(asset_name) != asset_name
        ):
            raise ValidationError("JSON 文档资源字段无效。")
        if kind == "image" and asset_name is None:
            raise ValidationError("JSON 图片块缺少资源名称。")
        rows_are_valid = isinstance(rows, list) and all(
            isinstance(row, list) and all(isinstance(cell, str) for cell in row) for row in rows
        )
        if not rows_are_valid:
            raise ValidationError("JSON 文档表格字段无效。")
        blocks.append(Block(kind, text, level, rows, asset_name))
    return blocks


def _json_assets(source: Path, payload: object) -> tuple[list[Asset], set[str], list[WarningItem]]:
    if not isinstance(payload, list):
        raise ValidationError("JSON 文档资源字段无效。")
    assets: list[Asset] = []
    available_names: set[str] = set()
    warnings: list[WarningItem] = []
    asset_directory = source.parent.parent / "assets"
    for item in payload:
        if not isinstance(item, dict):
            raise ValidationError("JSON 文档资源字段无效。")
        name = item.get("name")
        if not isinstance(name, str) or not name or safe_name(name) != name:
            raise ValidationError("JSON 文档资源名称无效。")
        if item.get("path") != f"assets/{name}":
            raise ValidationError("JSON 文档资源路径无效。")
        asset_path = asset_directory / name
        if not asset_path.is_file() or asset_path.is_symlink():
            warnings.append(WarningItem("JSON_ASSET_UNAVAILABLE", f"资源 {name} 未找到，已跳过。"))
            continue
        if asset_path.stat().st_size > MAX_COMPRESSED_BYTES:
            warnings.append(
                WarningItem("JSON_ASSET_UNAVAILABLE", f"资源 {name} 超过大小限制，已跳过。")
            )
            continue
        assets.append(Asset(name, asset_path.read_bytes()))
        available_names.add(name)
    return assets, available_names, warnings


def _remove_unavailable_images(
    blocks: list[Block], available_names: set[str]
) -> tuple[list[Block], int]:
    filtered = [
        block
        for block in blocks
        if block.kind != "image" or block.asset_name in available_names
    ]
    return filtered, len(blocks) - len(filtered)


def _json_warnings(payload: object) -> list[WarningItem]:
    if not isinstance(payload, list):
        raise ValidationError("JSON 文档警告字段无效。")
    warnings: list[WarningItem] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValidationError("JSON 文档警告字段无效。")
        code = item.get("code")
        message = item.get("message")
        location = item.get("location")
        if (
            not isinstance(code, str)
            or not code
            or not isinstance(message, str)
            or not message
            or (location is not None and not isinstance(location, str))
        ):
            raise ValidationError("JSON 文档警告字段无效。")
        warnings.append(WarningItem(code, message, location))
    return warnings


def parse_json(source: Path) -> ParsedDocument:
    try:
        payload = json.loads(source.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("JSON 文件无法解析。") from error
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValidationError("仅支持 schema_version 为 1 的廾匸转换 JSON 文件。")
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip() or len(title) > 1_000:
        raise ValidationError("JSON 文档标题无效。")
    assets, available_names, asset_warnings = _json_assets(source, payload.get("assets", []))
    warnings = _json_warnings(payload.get("warnings", [])) + asset_warnings
    blocks, skipped_images = _remove_unavailable_images(
        _json_blocks(payload.get("blocks")), available_names
    )
    sheets_payload = payload.get("sheets", {})
    if not isinstance(sheets_payload, dict) or any(
        not isinstance(name, str) or not name for name in sheets_payload
    ):
        raise ValidationError("JSON 文档工作表字段无效。")
    sheets: dict[str, list[Block]] = {}
    for name, sheet_payload in sheets_payload.items():
        sheet_blocks, skipped = _remove_unavailable_images(
            _json_blocks(sheet_payload), available_names
        )
        sheets[name] = sheet_blocks
        skipped_images += skipped
    if skipped_images:
        warnings.append(WarningItem("JSON_ASSET_UNAVAILABLE", "部分图片资源未找到，已跳过。"))
    return ParsedDocument(
        title.strip(), "json", blocks, sheets=sheets, assets=assets, warnings=warnings
    )


def parse_source(source: Path) -> ParsedDocument:
    parsers = {
        ".docx": parse_docx,
        ".pptx": parse_pptx,
        ".xlsx": parse_xlsx,
        ".pdf": parse_pdf,
        ".txt": parse_txt,
        ".csv": parse_csv,
        ".md": parse_markdown,
        ".json": parse_json,
    }
    return parsers[source.suffix.lower()](source)
