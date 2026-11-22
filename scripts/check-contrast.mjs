#!/usr/bin/env node
// 학생 화면 공용 디자인(activities/student-ui.css)의 색 대비 검사 — 외부 의존성 없음
// 사용: node scripts/check-contrast.mjs [css 경로]
// 기준(WCAG 2.1): 글자 4.5:1(1.4.3), 차트·상태 막대·입력 테두리·초점 링 3:1(1.4.11)
// 밝은 모드는 첫 :root 블록, 어두운 모드는 @media (prefers-color-scheme: dark) 안의 블록을 밝은 값 위에 덮어 계산한다.
// 색 형식: #rgb, #rrggbb, rgb(), hsl(), oklch()(tweakcn이 내는 형식). var(--x) 별칭은 따라가 푼다.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const file = process.argv[2] || path.join(here, "..", "activities", "student-ui.css");
const css = readFileSync(file, "utf8").replace(/\/\*[\s\S]*?\*\//g, "");

function blockAfter(src, idx) { const s = src.indexOf("{", idx); let d = 0;
  for (let i = s; i < src.length; i++) { if (src[i] === "{") d++; else if (src[i] === "}" && --d === 0) return src.slice(s + 1, i); } return ""; }
function decls(block) { const o = {}; for (const m of block.matchAll(/--([\w-]+)\s*:\s*([^;]+);?/g)) o[m[1]] = m[2].trim(); return o; }

const darkAt = css.search(/@media\s*\(prefers-color-scheme:\s*dark\)/);
const light = decls(blockAfter(css, css.indexOf(":root")));
const dark = darkAt >= 0 ? decls(blockAfter(css, css.indexOf("{", darkAt) + 1)) : {};
// 별칭 블록(두 번째 이후의 :root)도 함께 읽는다
let rest = css.slice(darkAt >= 0 ? darkAt : 0), alias = {}, k;
while ((k = rest.search(/(^|[^-\w]):root\s*\{/)) >= 0) { Object.assign(alias, decls(blockAfter(rest, k))); rest = rest.slice(rest.indexOf("{", k) + 1); }

function oklchToRgb(L, C, h) {
  const a = C * Math.cos(h * Math.PI / 180), b = C * Math.sin(h * Math.PI / 180);
  const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3, m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3, s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3;
  const lin = [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s, -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s];
  return lin.map(x => { x = Math.min(1, Math.max(0, x)); return 255 * (x <= 0.0031308 ? 12.92 * x : 1.055 * x ** (1 / 2.4) - 0.055); });
}
function hslToRgb(h, s, l) { s /= 100; l /= 100; const f = n => { const k = (n + h / 30) % 12, a = s * Math.min(l, 1 - l); return 255 * (l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1))); }; return [f(0), f(8), f(4)]; }
function parse(v) {
  v = v.trim().toLowerCase(); let m;
  if ((m = v.match(/^#([0-9a-f]{3})$/))) return [...m[1]].map(c => parseInt(c + c, 16));
  if ((m = v.match(/^#([0-9a-f]{6})/))) return [0, 2, 4].map(i => parseInt(m[1].slice(i, i + 2), 16));
  if ((m = v.match(/^rgba?\(\s*([\d.]+)[ ,]+([\d.]+)[ ,]+([\d.]+)/))) return m.slice(1, 4).map(Number);
  if ((m = v.match(/^hsla?\(\s*([\d.]+)(?:deg)?[ ,]+([\d.]+)%[ ,]+([\d.]+)%/))) return hslToRgb(+m[1], +m[2], +m[3]);
  if ((m = v.match(/^oklch\(\s*([\d.]+)(%?)\s+([\d.]+)\s+([\d.]+)/))) return oklchToRgb(m[2] ? m[1] / 100 : +m[1], +m[3], +m[4]);
  return null;
}
function resolve(vars, name, seen = new Set()) {
  if (seen.has(name)) return null; seen.add(name); const v = vars[name]; if (v == null) return null;
  const m = v.match(/^var\(\s*--([\w-]+)\s*(?:,[^)]*)?\)$/); return m ? resolve(vars, m[1], seen) : v;
}
const lum = rgb => { const c = rgb.map(x => { x /= 255; return x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; }); return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]; };
const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };

const TEXT = [["foreground", "background"], ["foreground", "card"], ["muted-foreground", "card"], ["muted-foreground", "background"], ["muted-foreground", "muted"],
  ["faint", "background"], ["faint", "card"], ["primary-ink", "card"], ["primary-ink", "background"], ["primary-foreground", "primary"],
  ["secondary-foreground", "secondary"], ["accent-foreground", "accent"], ["foreground", "info-bg"], ["good", "good-bg"], ["bad", "bad-bg"], ["warn", "warn-bg"],
  ["mint-d", "mint"], ["sky-d", "sky"], ["lemon-d", "lemon"], ["coral-d", "coral"], ["lav-d", "lav"], ["chart-3", "card"]];
const UI = [1, 2, 3, 4, 5].map(i => [`chart-${i}`, "card"]).concat([["success", "card"], ["warning", "card"], ["danger", "card"], ["input", "card"], ["ring", "background"], ["ring", "card"]]);

let fails = 0;
for (const [mode, vars] of [["밝은 모드", { ...light, ...alias }], ["어두운 모드", { ...light, ...dark, ...alias }]]) {
  console.log(`\n${mode}`);
  for (const [list, need] of [[TEXT, 4.5], [UI, 3]]) for (const [fg, bg] of list) {
    const a = resolve(vars, fg), b = resolve(vars, bg);
    if (!a || !b) { console.log(`  - ${fg}/${bg}: 토큰 없음(건너뜀)`); continue; }
    const ca = parse(a), cb = parse(b); if (!ca || !cb) { console.log(`  ? ${fg}/${bg}: 읽을 수 없는 색 ${a} / ${b}`); continue; }
    const r = ratio(ca, cb), ok = r >= need; if (!ok) fails++;
    console.log(`  ${ok ? "✓" : "✗"} ${(fg + " / " + bg).padEnd(34)} ${r.toFixed(2)}:1 (기준 ${need}:1)`);
  }
}
console.log(fails ? `\n기준 미달 ${fails}건` : "\n모두 기준 통과"); process.exit(fails ? 1 : 0);
