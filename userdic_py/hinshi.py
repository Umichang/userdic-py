from __future__ import annotations

from importlib.resources import files
from pathlib import Path

TYPES = ["generic", "mozc", "anthy", "atok", "msime", "wnn"]


def _load_hinshi_lines(path: Path) -> list[str]:
    rows: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        rows.append(s)
    return rows


def _make_hash(rows: list[str], from_idx: int, to_idx: int) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for row in rows:
        cols = row.split()
        if cols[from_idx].startswith("*"):
            continue
        fword = cols[from_idx].lstrip("*").split("/")[0]
        tword = cols[to_idx].lstrip("*").split("/")[0]
        mapping[fword] = tword
    return mapping


def load_hinshi_tables(base_dir: Path | None = None) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    hinshi_path = base_dir / "hinshi" if base_dir else Path(str(files("userdic_py").joinpath("hinshi")))
    rows = _load_hinshi_lines(hinshi_path)
    hinshi_f: dict[str, dict[str, str]] = {}
    hinshi_t: dict[str, dict[str, str]] = {}
    for i, dic_type in enumerate(TYPES):
        hinshi_f[dic_type] = _make_hash(rows, i, 0)
        hinshi_t[dic_type] = _make_hash(rows, 0, i)
    return hinshi_f, hinshi_t
