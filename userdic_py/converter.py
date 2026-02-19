from __future__ import annotations

import argparse
import plistlib
import sys
from pathlib import Path

from .hinshi import load_hinshi_tables
from .normkana import norm_kana

SUPPORTED = {"mozc", "google", "anthy", "canna", "atok", "msime", "wnn", "apple", "generic"}


def parse_record(dic_type: str, line: str, hinshi_f: dict[str, dict[str, str]]) -> str | None:
    s = line.strip()
    if not s or s.startswith("!") or s.startswith("\\"):
        return None

    if dic_type in {"generic", "mozc", "msime", "wnn"}:
        pron, word, prop = (s.split("\t") + [None, None, None])[:3]
        prop_norm = hinshi_f[dic_type].get(prop or "")
    elif dic_type == "google":
        return parse_record("mozc", s, hinshi_f)
    elif dic_type == "atok":
        if "\t" not in s:
            s = s.replace("､", "\t").replace(",", "\t")
        pron, word, prop = (s.split("\t") + [None, None, None])[:3]
        pron = norm_kana(pron or "")
        if prop:
            prop = prop.rstrip("*")
        prop_norm = hinshi_f[dic_type].get(prop or "")
    elif dic_type == "anthy":
        cols = s.split()
        pron, prop, word = (cols + [None, None, None])[:3]
        if prop:
            prop = prop.replace("#", "").split("*")[0]
        prop_norm = hinshi_f[dic_type].get(prop or "")
    elif dic_type == "canna":
        return parse_record("anthy", s, hinshi_f)
    elif dic_type == "apple":
        pron, word = (s.split("\t") + [None, None])[:2]
        prop_norm = "名詞"
    else:
        raise ValueError(f"{dic_type}: not supported yet")

    if word is None:
        print(f"{s}: incorrect record", file=sys.stderr)
        return None
    if prop_norm is None:
        print(f"{s}: Unknown 品詞: {prop}", file=sys.stderr)
        prop_norm = "名詞"
    return f"{pron}\t{word}\t{prop_norm}"


def format_record(dic_type: str, line: str, hinshi_t: dict[str, dict[str, str]]) -> str | None:
    if line is None:
        return None
    pron, word, prop = line.split("\t")
    if dic_type in {"generic", "mozc", "atok", "msime", "wnn"}:
        return f"{pron}\t{word}\t{hinshi_t[dic_type][prop]}"
    if dic_type == "apple":
        return f"{pron}\t{word}"
    if dic_type == "anthy":
        return f"{pron} #{hinshi_t[dic_type][prop]}*500 {word}"
    if dic_type == "google":
        return format_record("mozc", line, hinshi_t)
    if dic_type == "canna":
        return format_record("anthy", line, hinshi_t)
    raise ValueError(f"{dic_type}: not supported yet")


def header(dic_type: str, n: int) -> str | None:
    if dic_type == "msime":
        return "!Microsoft IME Dictionary Tool"
    if dic_type == "atok":
        return "!!ATOK_TANGO_TEXT_HEADER_1"
    if dic_type == "wnn":
        return f"\\comment \n\\total {n}\n"
    return None


def decode_input(raw: bytes) -> str:
    for enc in ["utf-16", "cp932", "euc_jp", "utf-8"]:
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def load_records(dic_type: str, raw: bytes, hinshi_f: dict[str, dict[str, str]]) -> list[str]:
    if dic_type == "apple":
        plist = plistlib.loads(raw)
        lines = [f"{d.get('shortcut', '')}\t{d.get('phrase', '')}" for d in plist if isinstance(d, dict)]
    else:
        lines = decode_input(raw).splitlines()
    out = [parse_record(dic_type, line, hinshi_f) for line in lines]
    return [x for x in out if x is not None]


def dump_records(dic_type: str, records: list[str], hinshi_t: dict[str, dict[str, str]]) -> bytes:
    lines = [header(dic_type, len(records))] + [format_record(dic_type, r, hinshi_t) for r in records]
    lines = [x for x in lines if x is not None]

    if dic_type == "apple":
        payload = []
        for line in lines:
            pron, word = line.split("\t")
            payload.append({"phrase": word, "shortcut": pron})
        return plistlib.dumps(payload, fmt=plistlib.FMT_XML, sort_keys=False)

    text = "\n".join(lines) + "\n"
    if dic_type == "msime":
        return b"\xff\xfe" + text.encode("utf-16-le")
    if dic_type == "atok":
        return text.encode("utf-16")
    if dic_type in {"wnn", "canna"}:
        return text.encode("euc_jp", errors="replace")
    return text.encode("utf-8", errors="replace")


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="userdic-py", description="Convert Japanese IM dictionary files")
    parser.add_argument("from_type")
    parser.add_argument("to_type")
    parser.add_argument("--base-dir", default=str(Path(__file__).resolve().parents[2]))
    args = parser.parse_args(argv)

    if args.from_type not in SUPPORTED or args.to_type not in SUPPORTED:
        parser.error("from/to must be one of: mozc, google, anthy, canna, atok, msime, wnn, apple, generic")

    hinshi_f, hinshi_t = load_hinshi_tables(Path(args.base_dir))
    records = load_records(args.from_type, sys.stdin.buffer.read(), hinshi_f)
    sys.stdout.buffer.write(dump_records(args.to_type, records, hinshi_t))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
