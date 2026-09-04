from __future__ import annotations

import tkinter as tk
from pathlib import Path

from office_to_markdown.models import BatchItem, BatchStatus, ConversionResult
from office_to_markdown.ui.state import UiPhase, UiState


def test_ui_state_defaults_and_option_mapping(tmp_path: Path) -> None:
    output = tmp_path / "output"
    vault = tmp_path / "vault"
    output.mkdir()
    vault.mkdir()
    state = UiState(tk.Tcl())

    assert state.phase is UiPhase.IDLE
    assert state.recursive.get() is False
    assert state.can_start is False

    state.sources.append(tmp_path / "source.docx")
    state.output.set(str(output))
    state.obsidian.set(True)
    state.include_source_link.set(True)
    state.copy_source.set(True)
    state.export_pptx_png.set(True)
    state.export_pptx_pdf.set(True)
    state.vault_root.set(str(vault))

    options = state.build_options()

    assert state.can_start is True
    assert options.tags == ("office-import",)
    assert options.obsidian_mode is True
    assert options.include_frontmatter is True
    assert options.source_link_root == vault
    assert options.copy_source is True
    assert options.export_pptx_png is True
    assert options.export_pptx_pdf is True


def test_ui_state_owns_ordered_sources_results_and_phases(tmp_path: Path) -> None:
    state = UiState(tk.Tcl())
    first = tmp_path / "first.docx"
    second = tmp_path / "second.pptx"

    state.add_sources((second, first, second))
    assert state.sources == [second, first]

    result = ConversionResult(tmp_path / "output", tmp_path / "report.md", ())
    item = BatchItem(second, BatchStatus.WARNING, result=result)
    state.apply_item(item)
    state.select(second)
    state.set_phase(UiPhase.RUNNING)
    assert state.selected_item == item
    assert state.phase is UiPhase.RUNNING
    assert state.can_cancel is True

    state.set_phase(UiPhase.CANCELLING)
    assert state.can_cancel is False
    state.set_phase(UiPhase.COMPLETED)
    assert state.can_edit is True
