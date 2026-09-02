from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from .models import BatchItem, BatchResult, BatchStatus, ConversionOptions
from .security import ALLOWED_SUFFIXES, ValidationError, safe_name
from .service import ConversionService


def discover_sources(directory: Path, recursive: bool = False) -> tuple[Path, ...]:
    entries = directory.rglob("*") if recursive else directory.glob("*")
    return tuple(
        sorted(
            (
                path
                for path in entries
                if path.is_file() and path.suffix.lower() in ALLOWED_SUFFIXES
            ),
            key=lambda path: path.name.lower(),
        )
    )


class BatchConversionService:
    def __init__(self, converter: ConversionService | None = None) -> None:
        self._converter = converter or ConversionService()
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def convert(
        self,
        sources: tuple[Path, ...],
        output_parent: Path,
        options: ConversionOptions | None = None,
        on_item: Callable[[BatchItem], None] | None = None,
    ) -> BatchResult:
        started_at = datetime.now().astimezone()
        items: list[BatchItem] = []
        for source in sources:
            if self._cancelled:
                item = BatchItem(source, BatchStatus.CANCELLED)
                items.append(item)
                if on_item:
                    on_item(item)
                continue
            if (output_parent / f"{safe_name(source.stem)}-markdown").exists():
                item = BatchItem(
                    source,
                    BatchStatus.SKIPPED,
                    error_code="OUTPUT_EXISTS",
                    error_message="输出目录已存在。",
                )
                items.append(item)
                if on_item:
                    on_item(item)
                continue
            if on_item:
                on_item(BatchItem(source, BatchStatus.RUNNING))
            try:
                result = self._converter.convert(source, output_parent, options)
                status = BatchStatus.WARNING if result.warnings else BatchStatus.SUCCESS
                item = BatchItem(source, status, result=result)
            except ValidationError as error:
                item = BatchItem(
                    source,
                    BatchStatus.FAILED,
                    error_code="VALIDATION_ERROR",
                    error_message=str(error),
                )
            except Exception:
                item = BatchItem(
                    source,
                    BatchStatus.FAILED,
                    error_code="CONVERSION_FAILED",
                    error_message="文件转换失败。",
                )
            items.append(item)
            if on_item:
                on_item(item)
        return BatchResult(tuple(items), started_at, datetime.now().astimezone())
