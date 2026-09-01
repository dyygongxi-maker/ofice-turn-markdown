import zipfile
from pathlib import Path

import pytest
from docx import Document
from openpyxl import Workbook
from pptx import Presentation

from office_to_markdown.security import ValidationError
from office_to_markdown.service import ConversionService


def test_rejects_non_office_input(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("not an office file", encoding="utf-8")
    with pytest.raises(ValidationError, match="Only DOCX"):
        ConversionService().convert(source, tmp_path)


def test_pyinstaller_entrypoint_uses_an_absolute_package_import() -> None:
    launcher = Path("src/launcher.py").read_text(encoding="utf-8")
    assert "from office_to_markdown.app import main" in launcher
    assert "from .app import main" not in launcher


def test_desktop_ui_uses_packageable_qt_runtime() -> None:
    app_module = Path("src/office_to_markdown/app.py").read_text(encoding="utf-8")
    assert "from PySide6.QtWidgets import" in app_module
    assert "import tkinter" not in app_module


def test_rejects_extension_content_mismatch_and_macros(tmp_path: Path) -> None:
    mismatch = tmp_path / "not-a-document.docx"
    with zipfile.ZipFile(mismatch, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("xl/workbook.xml", "<workbook/>")
    with pytest.raises(ValidationError, match="does not match"):
        ConversionService().convert(mismatch, tmp_path)

    macro = tmp_path / "macro.docx"
    with zipfile.ZipFile(macro, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
        archive.writestr("word/vbaProject.bin", b"macro")
    with pytest.raises(ValidationError, match="Macro-enabled"):
        ConversionService().convert(macro, tmp_path)


def test_converts_docx_to_markdown(tmp_path: Path) -> None:
    source = tmp_path / "brief.docx"
    document = Document()
    document.add_heading("Project Brief", level=1)
    document.add_paragraph("A local conversion test.")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Name"
    table.cell(0, 1).text = "Value"
    table.cell(1, 0).text = "Mode"
    table.cell(1, 1).text = "Local"
    document.save(source)

    result = ConversionService().convert(source, tmp_path)

    assert (result.output_path / "index.md").is_file()
    content = (result.output_path / "content.md").read_text(encoding="utf-8")
    assert "# Project Brief" in content
    assert "| Name | Value |" in content


def test_converts_pptx_to_markdown(tmp_path: Path) -> None:
    source = tmp_path / "slides.pptx"
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[1])
    slide.shapes.title.text = "Quarterly Notes"
    slide.placeholders[1].text = "First point\nSecond point"
    presentation.save(source)

    result = ConversionService().convert(source, tmp_path)

    content = (result.output_path / "slides.md").read_text(encoding="utf-8")
    assert "## Slide 1" in content
    assert "Quarterly Notes" in content


def test_converts_xlsx_and_warns_for_missing_formula_cache(tmp_path: Path) -> None:
    source = tmp_path / "budget.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Budget"
    sheet.append(["Item", "Amount"])
    sheet.append(["Hosting", 20])
    sheet["B3"] = "=SUM(B2:B2)"
    workbook.save(source)

    result = ConversionService().convert(source, tmp_path)

    sheet_markdown = (result.output_path / "sheets" / "Budget.md").read_text(encoding="utf-8")
    report = result.report_path.read_text(encoding="utf-8")
    assert "=SUM(B2:B2)" in sheet_markdown
    assert "XLSX_FORMULA_CACHE_UNAVAILABLE" in report


def test_does_not_overwrite_existing_output(tmp_path: Path) -> None:
    source = tmp_path / "duplicate.docx"
    Document().save(source)
    (tmp_path / "duplicate-markdown").mkdir()
    with pytest.raises(ValidationError, match="already exists"):
        ConversionService().convert(source, tmp_path)
