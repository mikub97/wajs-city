# Wajs City

Gra-prezent w stylu GTA: kolaż na wejściu, potem cztery etapy, każdy na osobnym ekranie.
Za każdy zaliczony etap jeden kupon PlayStation.

## Łańcuch, nie lista

W źródle strony jest **tylko pierwszy etap**. Definicja każdego kolejnego — pytanie, cele
strzelnicy, ścieżka do jego paczki, a gdy trzeba także jego klucz — siedzi w zaszyfrowanej
paczce etapu poprzedniego. Tak samo plansza końcowa. Nie da się więc podejrzeć, co dalej,
ani przeskoczyć etapu: żeby dostać etap N+1, trzeba rozwiązać etap N.

Każda paczka to **AES-256-GCM**, klucz z odpowiedzi gracza przez **PBKDF2-HMAC-SHA256**
(150 000 iteracji, losowa sól). Odszyfrowanie dzieje się w przeglądarce (WebCrypto).
Na serwerze nie ma ani haseł, ani ich hashy — poprawność weryfikuje tag GCM, więc strona
nie zna odpowiedzi.

```
assets/etap-N.enc:  "WAJS1" (5 B) | sól (16 B) | IV (12 B) | szyfrogram + tag
po odszyfrowaniu:   nagłówek JSON | 0x0A | bajty PDF-a
nagłówek:           {kod, plik, typ, nastepny: {...definicja kolejnego etapu...}, finisz?}
```

Hasło jest kanonizowane po obu stronach tak samo (`canonical()` w `tools/zbuduj_lancuch.py`
i `normalizuj()` w `index.html`): zostają wyłącznie znaki `[a-z0-9]`, więc wielkość liter,
spacje, interpunkcja i polskie ogonki nie mają znaczenia.

## Etapy

| # | Mechanika | Skąd bierze się klucz |
|---|---|---|
| 1 | pytanie otwarte | to, co gracz wpisze |
| 2 | pytanie otwarte | to, co gracz wpisze |
| 3 | strzelnica — jedna runda, cała ekipa na placu, trzeba ustrzelić wszystkich | klucz przyjeżdża w paczce etapu 2 |
| 4 | pytanie otwarte | to, co gracz wpisze |

Strzelnicy nie broni hasło, tylko sama gra: klucz jest w paczce poprzedniego etapu, więc nie
widać go w źródle, ale kto przejdzie etap 2, technicznie go ma. Dlatego siedzi tam najmniejszy
kupon. Twarze celów biorą się z `assets/ziomki/*.jpg`; brakujący plik nie psuje obrazka.

## Przebudowa łańcucha

Treść i hasła siedzą w `lancuch.json` — **plik zostaje lokalnie, nigdy w repo** (`.gitignore`).

```bash
python3 tools/zbuduj_lancuch.py lancuch.json
```

Builder odmawia pracy, jeśli dwa kupony mają ten sam kod. `tools/atrapa_pdf.py` generuje
PDF-atrapę do testów, zanim pojawią się prawdziwe kupony.

## Testy

```bash
node test-lancuch.mjs    # jsdom: cały łańcuch, strzelnica, pamięć postępu, brak wycieków
```

## Dźwięk

`assets/strzal.mp3` to próbka wystrzału (Freesound Community via Pixabay, CC0). Odtwarzana przez
WebAudio, żeby kolejne strzały mogły się nakładać bez opóźnienia. Gdyby plik się nie wczytał,
`syntezaStrzalu()` generuje huk z szumu i niskiego tonu — gra nie zostaje bez dźwięku.

Jawne PDF-y, wideo, oryginały zdjęć i `lancuch.json` nie wchodzą do repozytorium.
Strona wymaga `https://` (albo `localhost`) — WebCrypto nie działa z `file://`.
