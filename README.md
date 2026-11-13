# Wajs City

Jednostronicowa gra-prezent: cztery misje w stylistyce GTA, za każdą jeden kupon PlayStation.
Razem 350 zł (50 + 100 + 100 + 100).

## Jak to jest zabezpieczone

Kupony nie leżą tu jawnie. Każdy siedzi w osobnym pliku zaszyfrowanym **AES-256-GCM**, a klucz
powstaje z odpowiedzi gracza przez **PBKDF2-HMAC-SHA256** (150 000 iteracji, losowa sól).
Odszyfrowanie dzieje się dopiero w przeglądarce, przez WebCrypto. Na serwerze nie ma ani haseł,
ani ich hashy — poprawność weryfikuje sam tag GCM, więc **strona nie zna odpowiedzi** i nie da się
ich wyczytać z kodu.

```
assets/poziom-N.enc:  "WAJS1" (5 B) | sól (16 B) | IV (12 B) | szyfrogram + tag
po odszyfrowaniu:     nagłówek JSON | 0x0A | bajty PDF-a
```

Hasło jest kanonizowane po obu stronach tak samo (`canonical()` w `tools/encrypt.py`
i `normalizuj()` w `index.html`): zostają wyłącznie znaki `[a-z0-9]`, więc wielkość liter,
spacje, interpunkcja i polskie ogonki nie mają znaczenia.

## Misje

| # | Mechanika | Skąd bierze się hasło |
|---|---|---|
| 1 | pytanie otwarte | to, co gracz wpisze |
| 2 | strzelnica — 5 rund, w każdej 4 patrolujących glin z tabliczkami | sklejone odpowiedzi z pięciu rund |
| 3 | cheat code | wstukane słowo |
| 4 | pytanie otwarte | to, co gracz wpisze |

Minigra jest **sposobem wpisywania hasła**, nie bramką: sam fakt „wygranej" w JS niczego nie
odblokowuje, bo kupon i tak trzeba odszyfrować. Dlatego strzelnica ma pięć rund — przy jednej
rundzie cztery opcje oznaczałyby 25% na ślepo.

## Podmiana pytań i kuponów

Treść misji siedzi w tablicy `POZIOMY` na początku skryptu w `index.html`.
Po zmianie odpowiedzi trzeba przeszyfrować dany kupon:

```bash
python3 tools/make_payload.py kupon.pdf KOD-Z-KUPONU /tmp/p.bin
python3 tools/encrypt.py /tmp/p.bin assets/poziom-2.enc          # zapyta o hasło
python3 tools/encrypt.py --check assets/poziom-2.enc /tmp/p.bin  # round-trip
```

Dla strzelnicy hasłem jest ciąg poprawnych odpowiedzi w kolejności rund, np.
`"Tommy Vercetti 1986 V-Rock sześć Malibu Club"` — **dokładnie takich, jakie są na tabliczkach**.

`tools/atrapa_pdf.py` generuje podmieniony PDF do testów, zanim pojawią się prawdziwe kupony.

Jawne PDF-y i oryginalne materiały nie wchodzą do repozytorium (`.gitignore`).
Strona wymaga `https://` (albo `localhost`) — WebCrypto nie działa z `file://`.
