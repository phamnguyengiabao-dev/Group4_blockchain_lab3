from __future__ import annotations

import tempfile
import os
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import package_submission


class PackagingTests(unittest.TestCase):
    def test_rejects_unsafe_group_id(self) -> None:
        with self.assertRaises(Exception):
            package_submission.validate_group_id("../escape")
        with self.assertRaises(Exception):
            package_submission.validate_group_id("..")

    def test_package_shape_and_secret_exclusions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            code = root / "code"
            code.mkdir()
            (code / "main.py").write_text("print('ok')\n", encoding="utf-8")
            (code / "wallet.json").write_text("secret", encoding="utf-8")
            (code / ".venv").mkdir()
            (code / ".venv" / "secret.txt").write_text("secret", encoding="utf-8")
            report = root / "Report.pdf"
            report.write_bytes(b"%PDF-1.4 test")
            project = root / "project"
            project.mkdir()
            code.rename(project / "code")
            (project / "report").mkdir()
            report.rename(project / "report" / "Report.pdf")
            archive_path = root / "G01.zip"
            with patch.object(package_submission, "ROOT", project):
                archive = package_submission.package("G01", archive_path)
            with zipfile.ZipFile(archive) as stream:
                names = set(stream.namelist())
            self.assertEqual(names, {"G01/Code/main.py", "G01/Report.pdf"})

    def test_rejects_stale_report_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "code").mkdir()
            report_directory = root / "report"
            report_directory.mkdir()
            report_pdf = report_directory / "Report.pdf"
            report_source = report_directory / "report.typ"
            report_pdf.write_bytes(b"%PDF-1.4 old")
            report_source.write_text("new source", encoding="utf-8")
            os.utime(report_pdf, (1, 1))
            os.utime(report_source, (2, 2))
            with patch.object(package_submission, "ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "older than"):
                    package_submission.package("G01", root / "G01.zip")


if __name__ == "__main__":
    unittest.main()
