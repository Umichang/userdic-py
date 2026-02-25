from __future__ import annotations

import argparse
import plistlib
import sys
import xml.etree.ElementTree as ET
from ._version import __version__
from .hinshi import load_hinshi_tables
from .normkana import norm_kana

SUPPORTED = {"mozc", "google", "anthy", "canna", "atok", "msime", "dctx", "wnn", "apple", "generic"}

DCTX_NS = "http://www.microsoft.com/ime/dctx"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


def parse_record(dic_type: str, line: str, hinshi_f: dict[str, dict[str, str]]) -> str | None:
    s = line.strip().lstrip("\ufeff")
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
    if dic_type in {"generic", "mozc", "atok", "msime", "dctx", "wnn"}:
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


def parse_dctx_records(raw: bytes, hinshi_f: dict[str, dict[str, str]]) -> list[str]:
    text = decode_input(raw, "msime")
    root = ET.fromstring(text)

    records: list[str] = []
    ns_words = root.findall(f".//{{{DCTX_NS}}}Word")
    words = ns_words if ns_words else root.findall(".//Word")
    for elem in words:
        pron = (elem.findtext(f"{{{DCTX_NS}}}Reading") or elem.findtext("Reading") or "").strip()
        word = (elem.findtext(f"{{{DCTX_NS}}}Text") or elem.findtext("Text") or "").strip()
        prop = (elem.findtext(f"{{{DCTX_NS}}}PartOfSpeech") or elem.findtext("PartOfSpeech") or "").strip()
        line = parse_record("msime", f"{pron}\t{word}\t{prop}", hinshi_f)
        if line is not None:
            records.append(line)
    return records


def dump_dctx_records(records: list[str], hinshi_t: dict[str, dict[str, str]]) -> bytes:
    def esc(value: str) -> str:
        return (
            value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    lines = [
        '<?xml version="1.0" encoding="utf-16le"?>',
        f'<ns1:Dictionary xmlns:ns1="{DCTX_NS}" xmlns:xsi="{XSI_NS}">',
        "<ns1:Words>",
    ]

    for line in records:
        pron, word, prop = line.split("\t")
        lines.extend(
            [
                "<ns1:Word>",
                f"<ns1:Reading>{esc(pron)}</ns1:Reading>",
                f"<ns1:Text>{esc(word)}</ns1:Text>",
                f"<ns1:PartOfSpeech>{esc(hinshi_t['msime'][prop])}</ns1:PartOfSpeech>",
                "</ns1:Word>",
            ]
        )

    lines.extend(["</ns1:Words>", "</ns1:Dictionary>"])
    text = "\r\n".join(lines) + "\r\n"
    return b"\xff\xfe" + text.encode("utf-16-le")


def decode_input(raw: bytes, dic_type: str) -> str:
    # Keep compatibility with the original implementation order so UTF-16LE
    # text without BOM is not decoded as UTF-8 with embedded NUL bytes.
    encodings = ["utf-16", "cp932", "euc_jp", "utf-8"]
    if dic_type == "msime":
        # MS-IME dictionaries may be UTF-16 or UTF-8. For UTF-8 input,
        # blindly decoding with UTF-16 can succeed but produce mojibake.
        #
        # 1. BOM always wins.
        # 2. If NUL bytes are present, prefer UTF-16LE as a strong signal.
        # 3. Otherwise, prefer UTF-8 then legacy Japanese encodings.
        if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            return raw.decode("utf-16")
        if b"\x00" in raw:
            encodings = ["utf-16-le", "utf-8", "cp932", "euc_jp"]
        else:
            encodings = ["utf-8", "cp932", "euc_jp", "utf-16-le"]

    for enc in encodings:
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def load_records(dic_type: str, raw: bytes, hinshi_f: dict[str, dict[str, str]]) -> list[str]:
    if dic_type == "apple":
        plist = plistlib.loads(raw)
        lines = [f"{d.get('shortcut', '')}\t{d.get('phrase', '')}" for d in plist if isinstance(d, dict)]
    elif dic_type == "dctx":
        return parse_dctx_records(raw, hinshi_f)
    else:
        # Accept any newline style from input files (LF, CRLF, CR).
        text = decode_input(raw, dic_type).replace("\r\n", "\n").replace("\r", "\n")
        lines = text.split("\n")
    out = [parse_record(dic_type, line, hinshi_f) for line in lines]
    return [x for x in out if x is not None]


def dump_records(dic_type: str, records: list[str], hinshi_t: dict[str, dict[str, str]]) -> bytes:
    if dic_type == "dctx":
        return dump_dctx_records(records, hinshi_t)

    lines = [header(dic_type, len(records))] + [format_record(dic_type, r, hinshi_t) for r in records]
    lines = [x for x in lines if x is not None]

    if dic_type == "apple":
        payload = []
        for line in lines:
            pron, word = line.split("\t")
            payload.append({"phrase": word, "shortcut": pron})
        return plistlib.dumps(payload, fmt=plistlib.FMT_XML, sort_keys=False)

    newline = "\r\n" if dic_type in {"msime", "atok"} else "\n"
    text = newline.join(lines) + newline
    if dic_type == "msime":
        return b"\xff\xfe" + text.encode("utf-16-le")
    if dic_type == "atok":
        return text.encode("utf-16")
    if dic_type in {"wnn", "canna"}:
        return text.encode("euc_jp", errors="replace")
    return text.encode("utf-8", errors="replace")


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="userdic-py", description="Convert Japanese IM dictionary files")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("from_type")
    parser.add_argument("to_type")
    args = parser.parse_args(argv)

    if args.from_type not in SUPPORTED or args.to_type not in SUPPORTED:
        parser.error("from/to must be one of: mozc, google, anthy, canna, atok, msime, dctx, wnn, apple, generic")

    hinshi_f, hinshi_t = load_hinshi_tables()
    records = load_records(args.from_type, sys.stdin.buffer.read(), hinshi_f)
    sys.stdout.buffer.write(dump_records(args.to_type, records, hinshi_t))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
