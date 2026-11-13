#!/usr/bin/env python3
"""Sklada paczke, ktora potem szyfruje encrypt.py.

    naglowek-JSON (UTF-8) | 0x0A | surowe bajty PDF-a

Dzieki temu po odszyfrowaniu strona zna i kod kuponu, i sam plik -- a nic z tego
nie musi lezec jawnie w index.html.

    python3 tools/make_payload.py kupon.pdf XXXX-XXXX-XXXX /tmp/payload.bin
"""
import json
import sys

if len(sys.argv) != 4:
    sys.exit(__doc__)

pdf_path, code, out_path = sys.argv[1:]
header = json.dumps(
    {"kod": code, "plik": "prezent-anton.pdf", "typ": "application/pdf"},
    ensure_ascii=False,
    separators=(",", ":"),
).encode("utf-8")
assert b"\n" not in header
with open(out_path, "wb") as fh:
    fh.write(header + b"\n" + open(pdf_path, "rb").read())
print(f"OK: {out_path}, naglowek {len(header)} B")
