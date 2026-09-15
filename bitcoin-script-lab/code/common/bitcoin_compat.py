"""Load python-bitcoinlib reliably on Windows.

python-bitcoinlib 0.12.2 asks ctypes for legacy OpenSSL library names. Modern
Windows installations normally expose libcrypto-3 instead. This module maps
that lookup before any bitcoin wallet/key module is imported.
"""
from __future__ import annotations

import ctypes
import ctypes.util
import os
import sys
from pathlib import Path


def _find_windows_libcrypto() -> str | None:
    names = (
        "libcrypto-3-x64.dll",
        "libcrypto-3.dll",
        "libcrypto-1_1-x64.dll",
        "libeay32.dll",
        "libcrypto.dll",
    )
    preferred_directories = (
        Path(sys.base_prefix) / "DLLs",
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "mingw64" / "bin",
    )
    for directory in (*preferred_directories, *(Path(item) for item in os.environ.get("PATH", "").split(os.pathsep) if item)):
        for name in names:
            candidate = directory / name
            if candidate.is_file():
                return str(candidate)
    return None


def prepare_python_bitcoinlib() -> None:
    """Patch the legacy lookup only when it is broken on Windows."""
    if os.name != "nt" or ctypes.util.find_library("ssl"):
        return
    libcrypto = _find_windows_libcrypto()
    if not libcrypto:
        raise RuntimeError(
            "python-bitcoinlib needs OpenSSL libcrypto. Install Git for Windows "
            "or OpenSSL 3 and ensure its bin directory is on PATH."
        )
    original = ctypes.util.find_library

    def find_library(name: str) -> str | None:
        if name in {"ssl.35", "ssl"}:
            ssl = Path(os.path.dirname(libcrypto)) / "libssl-1_1.dll"
            return str(ssl) if ssl.is_file() else libcrypto
        if name in {"libeay32", "crypto"}:
            return libcrypto
        return original(name)

    ctypes.util.find_library = find_library


prepare_python_bitcoinlib()
