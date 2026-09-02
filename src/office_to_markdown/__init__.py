"""Local OOXML to Markdown conversion package."""

from .batch import BatchConversionService
from .service import ConversionService

__all__ = ["BatchConversionService", "ConversionService"]
