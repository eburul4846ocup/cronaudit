"""Export audit results to various file formats on disk."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from cronaudit.formatter import to_text, to_json, to_csv
from cronaudit.multi import AuditResult


@dataclass
class ExportOptions:
    output_dir: str = "."
    base_name: str = "cronaudit_report"
    formats: List[str] = None  # e.g. ["text", "json", "csv"]

    def __post_init__(self) -> None:
        if self.formats is None:
            self.formats = ["text"]


@dataclass
class ExportSummary:
    written: List[str]
    skipped: List[str]
    output_dir: str

    def __bool__(self) -> bool:
        return len(self.written) > 0


_FORMAT_RENDERERS = {
    "text": (to_text, ".txt"),
    "json": (to_json, ".json"),
    "csv": (to_csv, ".csv"),
}


def export_results(
    results: List[AuditResult],
    options: Optional[ExportOptions] = None,
    overwrite: bool = True,
) -> ExportSummary:
    """Render *results* in each requested format and write files to disk."""
    if options is None:
        options = ExportOptions()

    out_dir = Path(options.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written: List[str] = []
    skipped: List[str] = []

    for fmt in options.formats:
        fmt = fmt.lower()
        if fmt not in _FORMAT_RENDERERS:
            skipped.append(fmt)
            continue

        renderer, ext = _FORMAT_RENDERERS[fmt]
        file_path = out_dir / (options.base_name + ext)

        if file_path.exists() and not overwrite:
            skipped.append(str(file_path))
            continue

        content = renderer(results)
        file_path.write_text(content, encoding="utf-8")
        written.append(str(file_path))

    return ExportSummary(
        written=written,
        skipped=skipped,
        output_dir=str(out_dir),
    )
