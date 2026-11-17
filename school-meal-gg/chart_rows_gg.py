"""PRD 차트용 행: 제철 재료 4가지의 월별 등장 끼니, 칼슘 월별 중앙값."""
import re, json, collections as C, statistics as st
src = open("analyze_gg.py").read()
exec(src.split("N = len(meals)")[0])
def has(meal, pat):
    return any(re.search(pat, d) for d in meal["dishes"])
_s = src.split("SEASON = ")[1]; exec("S = " + _s[:_s.index("}\n") + 1])
mc = C.Counter(x["m"] for x in meals)
pick = [("subak", "수박", "수박"), ("gyul", "귤·감귤", "귤·감귤"), ("ttalgi", "딸기(생과)", "딸기(생과)"), ("bomnamul", "봄나물", "봄나물")]
out = []
for slug, key, name in pick:
    hit = C.Counter(x["m"] for x in meals if has(x, S[key]))
    for m in ORDER:
        out.append({"slug": slug, "name": name, "m": f"{m}월", "hits": hit[m], "meals": mc[m]})
json.dump(out, open("out/chart_season_rows.json", "w"), ensure_ascii=False)
cm = C.defaultdict(list)
for x in meals:
    if "칼슘(mg)" in x["ntr"]: cm[x["ymd"][:6]].append(x["ntr"]["칼슘(mg)"])
ca = [{"ym": f"{k[:4]}-{k[4:]}", "median": round(st.median(v)), "high": sum(a > 1020 for a in v), "meals": len(v)} for k, v in sorted(cm.items())]
json.dump(ca, open("out/chart_calcium_rows.json", "w"), ensure_ascii=False)
print(json.dumps(out, ensure_ascii=False)[:600]); print(json.dumps(ca, ensure_ascii=False)[:400])
print("SEASON keys", list(S)); print({k: S[k] for k, _, _ in [(p[1],0,0) for p in pick]})
