from __future__ import annotations

import argparse
import codecs
import plistlib
import sys
from ._version import __version__
from .hinshi import load_hinshi_tables
from .normkana import norm_kana

SUPPORTED = {"mozc", "google", "anthy", "canna", "atok", "msime", "wnn", "apple", "generic"}


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


def decode_input(raw: bytes, dic_type: str, input_encoding: str | None = None) -> str:
    if input_encoding is not None:
        try:
            return raw.decode(input_encoding)
        except UnicodeDecodeError as exc:
            raise ValueError(f"failed to decode input as {input_encoding}: {exc}") from exc

    # Keep compatibility with userdic-ng's fallback order while avoiding
    # Python's permissive utf-16 decode on non-UTF-16 byte streams.
    encodings = ["utf-16", "cp932", "euc_jp", "utf-8"]
    for enc in encodings:
        try:
            if enc == "utf-16" and not raw.startswith((b"\xff\xfe", b"\xfe\xff")) and b"\x00" not in raw:
                continue
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def load_records(
    dic_type: str,
    raw: bytes,
    hinshi_f: dict[str, dict[str, str]],
    input_encoding: str | None = None,
) -> list[str]:
    if dic_type == "apple":
        if input_encoding is not None:
            raise ValueError("--input-encoding is not supported with apple input")
        plist = plistlib.loads(raw)
        lines = [f"{d.get('shortcut', '')}\t{d.get('phrase', '')}" for d in plist if isinstance(d, dict)]
    else:
        # Accept any newline style from input files (LF, CRLF, CR).
        text = decode_input(raw, dic_type, input_encoding).replace("\r\n", "\n").replace("\r", "\n")
        lines = text.split("\n")
    out = [parse_record(dic_type, line, hinshi_f) for line in lines]
    return [x for x in out if x is not None]


def default_output_encoding(dic_type: str) -> str:
    if dic_type in {"msime", "atok"}:
        return "utf-16"
    if dic_type in {"wnn", "canna"}:
        return "euc_jp"
    return "utf-8"


def encode_text_output(text: str, encoding: str) -> bytes:
    return text.encode(encoding, errors="replace")


def dump_records(
    dic_type: str,
    records: list[str],
    hinshi_t: dict[str, dict[str, str]],
    output_encoding: str | None = None,
) -> bytes:
    lines = [header(dic_type, len(records))] + [format_record(dic_type, r, hinshi_t) for r in records]
    lines = [x for x in lines if x is not None]

    if dic_type == "apple":
        if output_encoding is not None:
            raise ValueError("--output-encoding is not supported with apple output")
        payload = []
        for line in lines:
            pron, word = line.split("\t")
            payload.append({"phrase": word, "shortcut": pron})
        return plistlib.dumps(payload, fmt=plistlib.FMT_XML, sort_keys=False)

    newline = "\r\n" if dic_type in {"msime", "atok"} else "\n"
    text = newline.join(lines) + newline
    return encode_text_output(text, output_encoding or default_output_encoding(dic_type))


def validate_encoding(name: str) -> str:
    try:
        codecs.lookup(name)
    except LookupError as exc:
        raise argparse.ArgumentTypeError(f"unknown encoding: {name}") from exc
    return name


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="userdic-py", description="Convert Japanese IM dictionary files")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--input-encoding", type=validate_encoding, help="read text input with the specified Python codec")
    parser.add_argument("--output-encoding", type=validate_encoding, help="write text output with the specified Python codec")
    parser.add_argument("from_type")
    parser.add_argument("to_type")
    args = parser.parse_args(argv)

    if args.from_type not in SUPPORTED or args.to_type not in SUPPORTED:
        parser.error("from/to must be one of: mozc, google, anthy, canna, atok, msime, wnn, apple, generic")
    if args.from_type == "apple" and args.input_encoding is not None:
        parser.error("--input-encoding is not supported with apple input")
    if args.to_type == "apple" and args.output_encoding is not None:
        parser.error("--output-encoding is not supported with apple output")

    hinshi_f, hinshi_t = load_hinshi_tables()
    try:
        records = load_records(args.from_type, sys.stdin.buffer.read(), hinshi_f, args.input_encoding)
        sys.stdout.buffer.write(dump_records(args.to_type, records, hinshi_t, args.output_encoding))
    except ValueError as exc:
        parser.exit(1, f"userdic-py: error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
