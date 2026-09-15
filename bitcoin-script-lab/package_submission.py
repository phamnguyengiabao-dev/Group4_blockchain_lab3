"""Build a regulation-compliant GroupID submission zip without secrets."""

from __future__ import annotations

import argparse
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def validate_group_id(group_id: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", group_id):
        raise ValueError("group_id may contain only letters, digits, underscore, and hyphen")
    return group_id

def package(group_id: str, output: Path | None = None) -> Path:
    group_id = validate_group_id(group_id)
    output = output or (ROOT / f"{group_id}.zip")
    report_pdf = ROOT / "report" / "Report.pdf"
    report_source = ROOT / "report" / "report.typ"
    if not report_pdf.is_file():
        raise FileNotFoundError("Create report/Report.pdf before packaging")
    if report_source.is_file() and report_source.stat().st_mtime > report_pdf.stat().st_mtime:
        raise RuntimeError(
            "report/Report.pdf is older than report/report.typ; close the PDF viewer, "
            "recompile the report, and package again"
        )
    with tempfile.TemporaryDirectory(prefix="lab03-package-") as temp:
        staging = Path(temp) / group_id
        shutil.copytree(ROOT / "code", staging / "Code", ignore=shutil.ignore_patterns(".venv", "__pycache__", ".pytest_cache", "*.pyc", "*.pyo", ".secrets", "wallet.json"))
        shutil.copy2(report_pdf, staging / "Report.pdf")
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for file in staging.rglob("*"):
                if file.is_file():
                    archive.write(file, file.relative_to(staging.parent))
    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("group_id")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(package(args.group_id, args.output))
