from __future__ import annotations

import json
import os
from pathlib import Path


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        local_data = Path(os.environ.get("LOCALAPPDATA", Path.home()))
        self.path = path or local_data / "廾匸转换" / "settings.json"

    def load_default_output(self) -> Path | None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            output = Path(data["default_output"])
        except (OSError, ValueError, KeyError, TypeError):
            return None
        return output if output.is_dir() else None

    def save_default_output(self, output: Path) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"default_output": str(output)}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
