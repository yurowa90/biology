#!/usr/bin/env node
/*
  NOAA CPC 해양 엘니뇨 지수(ONI)를 받아 data/oni.json 으로 저장하고,
  (옵션) 활동 HTML 안의 내장 스냅샷 블록을 같은 데이터로 교체합니다.

  사용:
    node scripts/fetch-oni.mjs                          # NOAA에서 받아 data/oni.json 갱신
    node scripts/fetch-oni.mjs --inject activities/enso.html
    node scripts/fetch-oni.mjs --from-file oni.ascii.txt --inject activities/enso.html
    node scripts/fetch-oni.mjs --strict                 # 실패 시 종료코드 1 (기본은 경고만 하고 0)

  - 외부 의존성 없음(Node 18+ 내장 fetch).
  - 기본 동작은 "실패해도 배포를 막지 않음": 받기/검증에 실패하면 기존 파일을 그대로 두고 경고만 출력합니다.
  - API 키·비밀값을 쓰지 않습니다.
*/
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt";
const OUT = "data/oni.json";
const SEASONS = ["DJF","JFM","FMA","MAM","AMJ","MJJ","JJA","JAS","ASO","SON","OND","NDJ"];
const MARK_START = "/*ONI_SNAPSHOT_START*/";
const MARK_END = "/*ONI_SNAPSHOT_END*/";

const args = process.argv.slice(2);
const opt = (name) => { const i = args.indexOf(name); return i >= 0 ? (args[i + 1] || "") : null; };
const strict = args.includes("--strict");
const injectPath = opt("--inject");
const fromFile = opt("--from-file");

function fail(msg) {
  console.warn("[fetch-oni] 경고: " + msg);
  console.warn("[fetch-oni] 기존 파일을 유지합니다.");
  process.exit(strict ? 1 : 0);
}

/* NOAA 형식:  " SEAS  YR   TOTAL   ANOM" 다음 줄부터 "  DJF 1950  24.72  -1.53" */
export function parseOni(text) {
  const series = [];
  const re = /^\s*([A-Z]{3})\s+(\d{4})\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*$/;
  for (const line of String(text).split(/\r?\n/)) {
    const m = line.match(re);
    if (!m) continue;
    const s = SEASONS.indexOf(m[1]);
    if (s < 0) continue;
    series.push([Number(m[2]), s, Number(m[4])]);
  }
  return series;
}

export function validate(series) {
  if (series.length < 600) return "행 수가 너무 적습니다(" + series.length + ")";
  for (const [y, s, a] of series) {
    if (!(y >= 1950 && y <= 2100)) return "연도 범위 이상: " + y;
    if (!(s >= 0 && s < 12)) return "계절 인덱스 이상: " + s;
    if (!(a > -5 && a < 5)) return "편차 값 이상: " + a;
  }
  return null;
}

async function getText() {
  if (fromFile) return readFile(fromFile, "utf8");
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 30000);
  try {
    const r = await fetch(ONI_URL, { signal: ctrl.signal, headers: { "User-Agent": "sci-textbook-oni-fetch/1.0" } });
    if (!r.ok) throw new Error("HTTP " + r.status);
    return await r.text();
  } finally { clearTimeout(timer); }
}

async function main() {
  let text;
  try { text = await getText(); }
  catch (e) { return fail("ONI 원본을 받지 못했습니다: " + (e && e.message || e)); }

  const series = parseOni(text);
  const bad = validate(series);
  if (bad) return fail("검증 실패 — " + bad);

  const first = series[0], last = series[series.length - 1];
  const doc = {
    schema: 1,
    source: "NOAA Climate Prediction Center — Oceanic Niño Index (ONI)",
    url: ONI_URL,
    fetchedAt: new Date().toISOString(),
    origin: fromFile ? "file" : "noaa",
    count: series.length,
    first: SEASONS[first[1]] + " " + first[0],
    last: SEASONS[last[1]] + " " + last[0],
    series
  };

  await mkdir(dirname(resolve(OUT)), { recursive: true });
  await writeFile(OUT, JSON.stringify(doc) + "\n", "utf8");
  console.log("[fetch-oni] " + OUT + " 저장: " + doc.count + "개 계절, " + doc.first + " ~ " + doc.last +
              " (최신 ONI " + last[2].toFixed(1) + ")");

  if (injectPath) {
    const html = await readFile(injectPath, "utf8");
    const i = html.indexOf(MARK_START), j = html.indexOf(MARK_END);
    if (i < 0 || j < i) return fail(injectPath + " 에서 스냅샷 표식을 찾지 못했습니다.");
    const block = MARK_START + "\nconst ONI_SNAPSHOT = " + JSON.stringify(doc) + ";\n";
    await writeFile(injectPath, html.slice(0, i) + block + html.slice(j), "utf8");
    console.log("[fetch-oni] " + injectPath + " 내장 스냅샷 갱신");
  }
}

// 모듈로 import 될 때(테스트)는 실행하지 않음
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main().catch((e) => fail(String(e && e.stack || e)));
}
