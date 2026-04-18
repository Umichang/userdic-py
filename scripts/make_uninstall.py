#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bindir", required=True)
    parser.add_argument("--libdir", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bindir = Path(args.bindir).expanduser().resolve()
    libdir = Path(args.libdir).expanduser().resolve()

    for name in ("userdic-py", "userdic-py.cmd"):
        target = bindir / name
        if target.exists() or target.is_symlink():
            target.unlink()

    shutil.rmtree(libdir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
