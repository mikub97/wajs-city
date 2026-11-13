#!/usr/bin/env python3
"""Generuje minimalny, poprawny PDF-atrape (jedna strona, kilka linii tekstu).

Sluzy wylacznie do testow, zanim pojawia sie prawdziwe kupony:

    python3 tools/atrapa_pdf.py /tmp/atrapa.pdf "ATRAPA" "tu wejdzie kupon na 50 zl"
"""
import sys


def build(lines):
    def esc(t):
        return t.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")

    body = ["BT", "/F1 22 Tf", "60 760 Td", "24 TL"]
    for i, line in enumerate(lines):
        body.append("(%s) Tj" % esc(line))
        if i != len(lines) - 1:
            body.append("T*")
    body.append("ET")
    content = "\n".join(body).encode("latin-1", "replace")

    objs = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]"
        b"/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>",
        b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>",
        b"<</Length %d>>stream\n" % len(content) + content + b"\nendstream",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for n, obj in enumerate(objs, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj" % n + obj + b"endobj\n"

    xref_at = len(out)
    out += b"xref\n0 %d\n" % (len(objs) + 1)
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer<</Size %d/Root 1 0 R>>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref_at)
    return bytes(out)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    open(sys.argv[1], "wb").write(build(sys.argv[2:]))
    print("OK:", sys.argv[1])
