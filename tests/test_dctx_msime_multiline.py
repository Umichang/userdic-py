from __future__ import annotations

import xml.etree.ElementTree as ET

from userdic_py.converter import dump_records, load_records
from userdic_py.hinshi import load_hinshi_tables


def test_multiline_msime_to_dctx_round_trip() -> None:
    hinshi_f, hinshi_t = load_hinshi_tables()

    msime_text = (
        "!Microsoft IME Dictionary Tool\r\n"
        "よみ1\t単語1\t名詞\r\n"
        "よみ2\t単語2\t固有名詞\r\n"
    )
    msime_bytes = b"\xff\xfe" + msime_text.encode("utf-16-le")

    records = load_records("msime", msime_bytes, hinshi_f)
    assert records == ["よみ1\t単語1\t名詞", "よみ2\t単語2\t固有名詞"]

    dctx_bytes = dump_records("dctx", records, hinshi_t)
    dctx_text = dctx_bytes[2:].decode("utf-16-le")
    assert dctx_text.startswith('<?xml version="1.0" encoding="utf-16le"?>')
    assert '<ns1:Dictionary xmlns:ns1="http://www.microsoft.com/ime/dctx" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' in dctx_text
    ET.fromstring(dctx_text)

    round_trip_records = load_records("dctx", dctx_bytes, hinshi_f)
    assert round_trip_records == records


def test_dctx_dump_sanitizes_invalid_xml_chars() -> None:
    _, hinshi_t = load_hinshi_tables()

    # XML 1.0 invalid char U+0001 should be removed so parser can load the result.
    records = ["よみ	語\x01彙	名詞"]
    dctx_bytes = dump_records("dctx", records, hinshi_t)
    dctx_text = dctx_bytes[2:].decode("utf-16-le")

    ET.fromstring(dctx_text)
    assert "\x01" not in dctx_text
