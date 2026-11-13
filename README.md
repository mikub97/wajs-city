# Wajs City

Jednostronicowa strona urodzinowa z prezentem zamkniętym za zagadką.

Prezent (PDF) nie leży tu jawnie — jest zaszyfrowany **AES-256-GCM**, a klucz powstaje z hasła
przez **PBKDF2-HMAC-SHA256** (150 000 iteracji, losowa sól). Całość odszyfrowuje się dopiero
w przeglądarce, przez WebCrypto, po wpisaniu poprawnej odpowiedzi. Na serwerze nie ma ani hasła,
ani jego hasha — poprawność weryfikuje sam tag GCM.

```
assets/prezent.enc:  "WAJS1" (5 B) | sól (16 B) | IV (12 B) | szyfrogram + tag
po odszyfrowaniu:    nagłówek JSON | 0x0A | bajty PDF-a
```

## Przygotowanie paczki od nowa

```bash
python3 tools/make_payload.py kupon.pdf KOD-KUPONU /tmp/payload.bin
python3 tools/encrypt.py /tmp/payload.bin assets/prezent.enc          # zapyta o hasło
python3 tools/encrypt.py --check assets/prezent.enc /tmp/payload.bin  # round-trip
```

Jawny PDF i paczka nie wchodzą do repozytorium (`.gitignore`). Strona wymaga `https://`
(albo `localhost`) — WebCrypto nie działa z `file://`.
