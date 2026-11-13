/* Testy lancucha etapow: prawdziwy index.html w jsdom. */
import { readFileSync } from "node:fs";
import { webcrypto } from "node:crypto";
import { createRequire } from "node:module";
const { JSDOM } = createRequire("/Users/m11/x.js")("jsdom");

const ROOT = "/Users/m11/Documents/codes/anton";
const html = readFileSync(`${ROOT}/index.html`, "utf8");
const skrypt = html.match(/<script>([\s\S]*?)<\/script>/)[1];

const wait = (ms) => new Promise(r => setTimeout(r, ms));
let fails = 0;
const check = (n, ok, extra = "") => { console.log(`${ok ? " OK  " : "FAIL "} ${n}${extra ? "  " + extra : ""}`); if (!ok) fails++; };

function nowaStrona(storage = {}) {
  const dom = new JSDOM(html, { runScripts: "outside-only", url: "https://wajs.test/", pretendToBeVisual: true });
  const w = dom.window;
  Object.defineProperty(w, "crypto", { value: webcrypto, configurable: true });
  w.TextEncoder = TextEncoder; w.TextDecoder = TextDecoder;
  if (!w.Blob) w.Blob = Blob;
  w.fetch = async (url) => {
    const buf = readFileSync(`${ROOT}/${url}`);
    return { ok: true, status: 200, arrayBuffer: async () => buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength) };
  };
  w.URL.createObjectURL = () => "blob:test";
  w.scrollTo = () => {};
  w.Element.prototype.scrollIntoView = function () {};
  for (const [k, v] of Object.entries(storage)) w.localStorage.setItem(k, v);
  w.eval(skrypt);
  return w;
}

async function odpowiedz(w, id, tekst) {
  const karta = w.document.getElementById("etap-" + id);
  karta.querySelector("input").value = tekst;
  karta.querySelector("form").dispatchEvent(new w.Event("submit", { cancelable: true, bubbles: true }));
  for (let i = 0; i < 60; i++) {
    await wait(100);
    const m = karta.querySelector(".msg").textContent;
    if (m && m !== "Sprawdzam…") break;
  }
  await wait(150);
  return {
    msg: karta.querySelector(".msg").textContent,
    otwarte: karta.querySelector(".nagroda").hidden === false,
    kod: (karta.querySelector(".code") || {}).textContent || "",
  };
}

async function wystrzelajWszystkich(w) {
  const karta = w.document.getElementById("etap-e3");
  // gracz strzela dalej mimo przeladowan, az plac bedzie pusty
  for (let proba = 0; proba < 120; proba++) {
    const zywe = [...karta.querySelectorAll(".cel")].filter(c => !c.classList.contains("trafiony"));
    if (!zywe.length) break;
    zywe[0].dispatchEvent(new w.MouseEvent("click", { bubbles: true, cancelable: true }));
    await wait(200);
  }
  for (let i = 0; i < 40; i++) {
    await wait(150);
    if (karta.querySelector(".nagroda").hidden === false) break;
  }
  return {
    otwarte: karta.querySelector(".nagroda").hidden === false,
    kod: (karta.querySelector(".code") || {}).textContent || "",
    msg: karta.querySelector(".msg").textContent,
    zywe: [...karta.querySelectorAll(".cel")].filter(c => !c.classList.contains("trafiony")).length,
  };
}

const widoczny = (w) => [...w.document.querySelectorAll(".ekran")].findIndex(e => e.classList.contains("on"));
const gwiazdki = (w) => [...w.document.querySelectorAll("#gwiazdki i")].map(g => g.classList.contains("on") ? "*" : ".").join("");

// ---------- 1. zrodlo strony nie zdradza dalszych etapow ----------
{
  check("w zrodle jest pytanie 1", html.includes("jak się witasz, Rumpert?"));
  check("w zrodle NIE MA pytania 2", !/KKK/i.test(html));
  check("w zrodle NIE MA pytania 4", !/z kim jazda/i.test(html));
  check("w zrodle NIE MA napisu koncowego", !/janami/i.test(html));
  check("w zrodle NIE MA zdjec strzelnicy", !/ziomki/i.test(html));
  check("w zrodle NIE MA sciezek do dalszych paczek", !/etap-2\.enc|etap-3\.enc|etap-4\.enc/.test(html));
  check("w zrodle NIE MA zadnego kodu kuponu", !/8QD3|ECXG|L54J|DXK4/.test(html));
  check("w zrodle NIE MA kwot", !/350|100 zł|50 zł/.test(html));
}

// ---------- 2. ekrany ----------
{
  const w = nowaStrona();
  await wait(300);
  check("start na ekranie 0 (kolaż)", widoczny(w) === 0);
  check("kolaż ma 4 zdjęcia", w.document.querySelectorAll("#ekran-0 .panel img").length === 4);
  check("etap 1 zbudowany, ale niewidoczny", !!w.document.getElementById("etap-e1") && widoczny(w) === 0);
  check("HUD ma 4 gwiazdki", gwiazdki(w) === "....", gwiazdki(w));

  w.document.getElementById("zaczynamy").dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  await wait(200);
  check("przycisk Zaczynamy przenosi na etap 1", widoczny(w) === 1);
  check("HUD pokazuje numer etapu", w.document.getElementById("etap-info").textContent === "Etap 1 z 4",
    w.document.getElementById("etap-info").textContent);
  check("na tym etapie nie ma jeszcze kolejnych ekranów", w.document.querySelectorAll(".ekran").length === 2);
}

// ---------- 3. lancuch ----------
{
  const w = nowaStrona();
  await wait(300);

  let r = await odpowiedz(w, "e1", "siemanko");
  check("e1 odrzuca zła odpowiedź", !r.otwarte, `-> ${r.msg}`);
  check("  WASTED", w.document.getElementById("wasted").classList.contains("on"));
  check("  nadal brak etapu 2", !w.document.getElementById("etap-e2"));

  r = await odpowiedz(w, "e1", "Essa, Glockboy!");
  check("e1 otwiera kupon", r.otwarte && r.kod === "8QD3-98AK-GR3A", `-> ${r.kod || r.msg}`);
  check("  gwiazdka 1", gwiazdki(w) === "*...", gwiazdki(w));
  check("  etap 2 przyjechał z kuponem", !!w.document.getElementById("etap-e2"));
  check("  i ma pytanie o KKK", w.document.querySelector("#etap-e2 .question").textContent === "co to jest KKK?",
    (w.document.querySelector("#etap-e2 .question") || {}).textContent);
  check("  pojawił się przycisk Dalej", !!w.document.querySelector("#ekran-1 .dalej"));

  w.document.querySelector("#ekran-1 .dalej").dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  await wait(150);
  check("  Dalej przenosi na etap 2", widoczny(w) === 2);

  r = await odpowiedz(w, "e2", "karol kurwa krzysztofik");
  check("e2 otwiera kupon", r.otwarte && r.kod === "ECXG-LCBN-H6DT", `-> ${r.kod || r.msg}`);
  check("  strzelnica przyjechała", !!w.document.getElementById("etap-e3"));
  check("  ma 6 celów ze zdjęciami", w.document.querySelectorAll("#etap-e3 .cel img").length === 6,
    String(w.document.querySelectorAll("#etap-e3 .cel").length));
  check("  gwiazdki 2", gwiazdki(w) === "**..", gwiazdki(w));

  const r3 = await wystrzelajWszystkich(w);
  check("strzelnica: wszyscy ustrzeleni otwierają kupon", r3.otwarte && r3.kod === "DXK4-H6L7-GTDP", `-> ${r3.kod || r3.msg} (zywych: ${r3.zywe})`);
  check("  etap 4 przyjechał", !!w.document.getElementById("etap-e4"));
  check("  i pyta o jazdę", (w.document.querySelector("#etap-e4 .question") || {}).textContent === "z kim jazda?");

  const r4 = await odpowiedz(w, "e4", "z Janami!");
  check("e4 otwiera ostatni kupon", r4.otwarte && r4.kod === "L54J-QR3E-QB65", `-> ${r4.kod || r4.msg}`);
  check("  cztery gwiazdki", gwiazdki(w) === "****", gwiazdki(w));
  check("  ekran finiszu zbudowany", !!w.document.getElementById("finisz"));
  check("  z napisem końcowym", w.document.querySelector("#finisz .wielkie").textContent === "No to jazda z Janami!");
  check("  i bez dopisku o etapach", !w.document.getElementById("finisz").textContent.includes("cztery kupony"), w.document.getElementById("finisz").textContent.trim());

  const kody = [...w.document.querySelectorAll(".code")].map(c => c.textContent);
  check("cztery różne kody", new Set(kody).size === 4 && kody.length === 4, kody.join(","));

  // ---------- 4. postep przezywa odswiezenie ----------
  const zapis = w.localStorage.getItem("wajs-city-postep");
  const w2 = nowaStrona({ "wajs-city-postep": zapis });
  await wait(3500);
  check("po odświeżeniu łańcuch się odtwarza", gwiazdki(w2) === "****", gwiazdki(w2));
  check("  wszystkie cztery kody wracają",
    [...w2.document.querySelectorAll(".code")].map(c => c.textContent).join(",") === kody.join(","),
    [...w2.document.querySelectorAll(".code")].map(c => c.textContent).join(","));
}

console.log(fails ? `\n${fails} TESTOW PADLO` : "\nWszystko OK");
process.exit(fails ? 1 : 0);
