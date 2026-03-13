from __future__ import annotations

import plistlib
import unittest

from userdic_py.converter import decode_input, dump_records, load_records, run
from userdic_py.hinshi import load_hinshi_tables


class ConverterEncodingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.hinshi_f, cls.hinshi_t = load_hinshi_tables()
        cls.generic_record = "あ\t亜\t名詞\r\n"

    def test_msime_utf16le_without_bom_is_decoded(self) -> None:
        raw = self.generic_record.encode("utf-16-le")
        records = load_records("msime", raw, self.hinshi_f)
        self.assertEqual(records, ["あ\t亜\t名詞"])

    def test_msime_utf8_uses_fallback_order_without_mojibake(self) -> None:
        raw = self.generic_record.encode("utf-8")
        records = load_records("msime", raw, self.hinshi_f)
        self.assertEqual(records, ["あ\t亜\t名詞"])

    def test_generic_utf8_uses_same_decode_path(self) -> None:
        raw = self.generic_record.encode("utf-8")
        records = load_records("generic", raw, self.hinshi_f)
        self.assertEqual(records, ["あ\t亜\t名詞"])

    def test_explicit_input_encoding_utf8(self) -> None:
        raw = self.generic_record.encode("utf-8")
        records = load_records("generic", raw, self.hinshi_f, input_encoding="utf-8")
        self.assertEqual(records, ["あ\t亜\t名詞"])

    def test_explicit_input_encoding_cp932(self) -> None:
        raw = self.generic_record.encode("cp932")
        records = load_records("generic", raw, self.hinshi_f, input_encoding="cp932")
        self.assertEqual(records, ["あ\t亜\t名詞"])

    def test_explicit_input_encoding_failure_is_error(self) -> None:
        raw = self.generic_record.encode("utf-8")
        with self.assertRaisesRegex(ValueError, "failed to decode input as cp932"):
            load_records("generic", raw, self.hinshi_f, input_encoding="cp932")

    def test_output_encoding_cp932(self) -> None:
        raw = dump_records("generic", ["あ\t亜\t名詞"], self.hinshi_t, output_encoding="cp932")
        self.assertEqual(raw, "あ\t亜\t名詞\n".encode("cp932", errors="replace"))

    def test_output_encoding_utf16le_has_no_bom(self) -> None:
        raw = dump_records("generic", ["あ\t亜\t名詞"], self.hinshi_t, output_encoding="utf-16-le")
        self.assertFalse(raw.startswith((b"\xff\xfe", b"\xfe\xff")))
        self.assertEqual(raw, "あ\t亜\t名詞\n".encode("utf-16-le"))

    def test_default_msime_output_keeps_bom_and_crlf(self) -> None:
        raw = dump_records("msime", ["あ\t亜\t名詞"], self.hinshi_t)
        self.assertTrue(raw.startswith(b"\xff\xfe"))
        self.assertIn("\r\n".encode("utf-16-le"), raw)

    def test_default_wnn_output_keeps_lf(self) -> None:
        raw = dump_records("wnn", ["あ\t亜\t名詞"], self.hinshi_t)
        self.assertNotIn(b"\r\n", raw)
        self.assertIn(b"\n", raw)

    def test_default_msime_to_apple_output_is_parseable(self) -> None:
        raw = dump_records("apple", ["あ\t亜\t名詞"], self.hinshi_t)
        payload = plistlib.loads(raw)
        self.assertEqual(payload, [{"phrase": "亜", "shortcut": "あ"}])

    def test_invalid_encoding_name_is_cli_error(self) -> None:
        with self.assertRaises(SystemExit) as exc:
            run(["--input-encoding", "not-a-real-encoding", "generic", "mozc"])
        self.assertEqual(exc.exception.code, 2)

    def test_apple_input_rejects_input_encoding(self) -> None:
        with self.assertRaises(SystemExit) as exc:
            run(["--input-encoding", "utf-8", "apple", "generic"])
        self.assertEqual(exc.exception.code, 2)

    def test_apple_output_rejects_output_encoding(self) -> None:
        with self.assertRaises(SystemExit) as exc:
            run(["--output-encoding", "utf-8", "generic", "apple"])
        self.assertEqual(exc.exception.code, 2)

    def test_decode_input_falls_back_to_utf8(self) -> None:
        text = decode_input(self.generic_record.encode("utf-8"), "generic")
        self.assertEqual(text, self.generic_record)


if __name__ == "__main__":
    unittest.main()
