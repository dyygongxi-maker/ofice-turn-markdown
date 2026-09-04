from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_ui_contracts_run_in_a_clean_tkinter_process() -> None:
    """Keep Tcl runtime teardown in existing UI tests from contaminating this suite."""
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("ui_contract_runner.py"))],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONUTF8": "1"},
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
