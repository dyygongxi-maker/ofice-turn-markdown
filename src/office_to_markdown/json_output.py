from __future__ import annotations

import json

from .models import Block, ParsedDocument


def _block_payload(block: Block) -> dict[str, object]:
    payload: dict[str, object] = {"kind": block.kind}
    if block.text:
        payload["text"] = block.text
    if block.level:
        payload["level"] = block.level
    if block.rows:
        payload["rows"] = block.rows
    if block.asset_name:
        payload["asset_name"] = block.asset_name
    return payload


def render_json(document: ParsedDocument) -> str:
    payload = {
        "schema_version": 1,
        "title": document.title,
        "source_format": document.format,
        "blocks": [_block_payload(block) for block in document.blocks],
        "sheets": {
            name: [_block_payload(block) for block in blocks]
            for name, blocks in document.sheets.items()
        },
        "assets": [
            {"name": asset.name, "path": f"assets/{asset.name}"} for asset in document.assets
        ],
        "warnings": [
            {"code": warning.code, "message": warning.message, "location": warning.location}
            for warning in document.warnings
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
