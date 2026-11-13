#!/usr/bin/env python3
"""Buduje lancuch zaszyfrowanych etapow z pliku lancuch.json.

Kazdy etap jest osobnym plikiem .enc. Po odszyfrowaniu zawiera:

    naglowek JSON | 0x0A | bajty PDF-a

a w naglowku siedzi definicja NASTEPNEGO etapu (pytanie, cele strzelnicy,
sciezka do jego .enc i - gdy trzeba - jego klucz). Dzieki temu w zrodle strony
jest tylko etap pierwszy: do kolejnych nie da sie dojsc inaczej niz przechodzac
poprzednie.

    python3 tools/zbuduj_lancuch.py lancuch.json

lancuch.json trzyma hasla, wiec NIE moze trafic do repozytorium (.gitignore).
"""
import hashlib
import json
import os
import sys
import unicodedata

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"WAJS1"
ITERATIONS = 150_000


def canonical(password: str) -> str:
    """MUSI byc identyczna z normalizuj() w index.html."""
    decomposed = unicodedata.normalize("NFD", password.lower()).replace("ł", "l")
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return "".join(ch for ch in stripped if ch.isalnum() and ch.isascii())


def zaszyfruj(haslo: str, naglowek: dict, pdf_path: str, out_path: str) -> None:
    tresc = json.dumps(naglowek, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    assert b"\n" not in tresc
    plain = tresc + b"\n" + open(pdf_path, "rb").read()

    salt, iv = os.urandom(16), os.urandom(12)
    key = hashlib.pbkdf2_hmac("sha256", canonical(haslo).encode("utf-8"), salt, ITERATIONS, dklen=32)
    blob = MAGIC + salt + iv + AESGCM(key).encrypt(iv, plain, None)
    open(out_path, "wb").write(blob)

    ma_nastepny = naglowek.get("nastepny") is not None
    print("OK %-22s %7d B  naglowek %4d B  nastepny: %s"
          % (out_path, len(blob), len(tresc), naglowek["nastepny"]["id"] if ma_nastepny else "brak (finisz)"))


def main(spec_path: str) -> None:
    spec = json.load(open(spec_path, encoding="utf-8"))
    etapy = spec["etapy"]

    kody = [e["kod"] for e in etapy]
    if len(set(kody)) != len(kody):
        sys.exit("BLAD: kupony maja powtarzajace sie kody: %s" % kody)

    for i, e in enumerate(etapy):
        naglowek = {
            "kod": e["kod"],
            "plik": e.get("nazwa", "kupon.pdf"),
            "typ": "application/pdf",
            "nastepny": etapy[i + 1]["definicja"] if i + 1 < len(etapy) else None,
        }
        if e.get("finisz"):
            naglowek["finisz"] = e["finisz"]
        zaszyfruj(e["haslo"], naglowek, e["pdf"], e["enc"])

    print("\nGotowe: %d etapow, kody unikalne." % len(etapy))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
