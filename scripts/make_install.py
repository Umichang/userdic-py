#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


UNIX_LAUNCHER = """#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / \"lib\" / \"userdic-py\"))

from userdic_py.converter import run

if __name__ == \"__main__\":
    raise SystemExit(run())
"""


WINDOWS_LAUNCHER_TEMPLATE = """@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
{python_launcher} -c "import os,pathlib,sys;script_dir=pathlib.Path(os.environ['SCRIPT_DIR']).resolve();sys.path.insert(0,str(script_dir.parent / 'lib' / 'userdic-py'));from userdic_py.converter import run;raise SystemExit(run(sys.argv[1:]))" %*
"""


def write_unix_launcher(path: Path) -> None:
    path.write_text(UNIX_LAUNCHER, encoding="utf-8")
    path.chmod(0o755)


def write_windows_launcher(path: Path, python_launcher: str) -> None:
    content = WINDOWS_LAUNCHER_TEMPLATE.format(python_launcher=python_launcher)
    path.write_text(content, encoding="utf-8", newline="\r\n")


def copy_package(repo_root: Path, libdir: Path) -> None:
    package_src = repo_root / "userdic_py"
    package_dst = libdir / "userdic_py"
    package_dst.mkdir(parents=True, exist_ok=True)

    for src in package_src.glob("*.py"):
        shutil.copy2(src, package_dst / src.name)
    shutil.copy2(package_src / "hinshi", package_dst / "hinshi")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bindir", required=True)
    parser.add_argument("--libdir", required=True)
    parser.add_argument("--windows-python-launcher", default="python")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    bindir = Path(args.bindir).expanduser().resolve()
    libdir = Path(args.libdir).expanduser().resolve()

    copy_package(repo_root, libdir)
    bindir.mkdir(parents=True, exist_ok=True)
    write_unix_launcher(bindir / "userdic-py")
    write_windows_launcher(bindir / "userdic-py.cmd", args.windows_python_launcher)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
