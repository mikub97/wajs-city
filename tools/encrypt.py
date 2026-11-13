#!/usr/bin/env python3
"""Szyfruje plik (np. PDF z kuponem) do formatu, ktory rozszyfruje index.html w przegladarce.

Format wyjsciowy:  b"WAJS1" (5B) | salt (16B) | iv (12B) | ciphertext+tag

    python3 tools/encrypt.py wejscie.pdf assets/prezent.enc
    python3 tools/encrypt.py --check assets/prezent.enc wejscie.pdf   # weryfikacja round-trip

Haslo podaje sie interaktywnie (getpass) albo przez $WAJS_PASSWORD. Nigdy nie jest zapisywane.
"""
import hashlib
import os
import sys
import unicodedata
from getpass import getpass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"WAJS1"
ITERATIONS = 150_000
SALT_LEN = 16
IV_LEN = 12


def canonical(password: str) -> str:
    """Kanoniczna postac hasla -- MUSI byc identyczna z normalizuj() w index.html.

    Zdejmuje wielkosc liter, diakrytyki, spacje i interpunkcje, zeby "Ala Ma Kota",
    "alamakota" i "ala, ma kota!" dawaly ten sam klucz.
    """
    decomposed = unicodedata.normalize("NFD", password.lower()).replace("\u0142", "l")
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return "".join(ch for ch in stripped if ch.isalnum() and ch.isascii())


def derive(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS, dklen=32)


def read_password(confirm: bool) -> str:
    pwd = os.environ.get("WAJS_PASSWORD") or getpass("Haslo: ")
    if confirm and not os.environ.get("WAJS_PASSWORD"):
        if getpass("Powtorz:  ") != pwd:
            sys.exit("Hasla sie nie zgadzaja.")
    if not canonical(pwd):
        sys.exit("Puste haslo.")
    return pwd


def encrypt(src: str, dst: str) -> None:
    plaintext = open(src, "rb").read()
    pwd = canonical(read_password(confirm=True))
    salt = os.urandom(SALT_LEN)
    iv = os.urandom(IV_LEN)
    blob = MAGIC + salt + iv + AESGCM(derive(pwd, salt)).encrypt(iv, plaintext, None)
    open(dst, "wb").write(blob)
    print(f"OK: {dst} ({len(blob)} B), zrodlo {len(plaintext)} B, sha256 zrodla {hashlib.sha256(plaintext).hexdigest()}")


def check(enc: str, src: str) -> None:
    blob = open(enc, "rb").read()
    if blob[:5] != MAGIC:
        sys.exit("Zly naglowek pliku.")
    salt = blob[5:5 + SALT_LEN]
    iv = blob[5 + SALT_LEN:5 + SALT_LEN + IV_LEN]
    ct = blob[5 + SALT_LEN + IV_LEN:]
    pwd = canonical(read_password(confirm=False))
    try:
        out = AESGCM(derive(pwd, salt)).decrypt(iv, ct, None)
    except Exception:
        sys.exit("NIE DA SIE ODSZYFROWAC tym haslem.")
    want = hashlib.sha256(open(src, "rb").read()).hexdigest()
    got = hashlib.sha256(out).hexdigest()
    print(f"oryginal: {want}\nodszyfr.: {got}\n{'ZGODNE -- round-trip OK' if want == got else 'ROZNE -- BLAD!'}")
    sys.exit(0 if want == got else 1)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--check"] and len(args) == 3:
        check(args[1], args[2])
    elif len(args) == 2:
        encrypt(args[0], args[1])
    else:
        sys.exit(__doc__)
