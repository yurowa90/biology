"""추가 검증: 2024년 3~4월 영양소 급변, 같은 달끼리 비교한 유행 추세, 학교 확산, 과일 분산 분해(분석 스크립트와 같은 사전)."""
import re, collections as C, statistics as st
FORCE_RAW = True  # 진단은 특이값 처리 전 원본으로 한다
src = open("analyze_gg.py").read()
exec(src.split("N = len(meals)")[0])
def has(meal, pat):
    return any(re.search(pat, d) for d in meal["dishes"])
G = {}
_g = src.split("GROUP = ")[1]; exec("G = " + _g[:_g.index("}\n") + 1])
T = {}
_t = src.split("TREND = ")[1]; exec("T = " + _t[:_t.index("}\n") + 1])
# 1. 영양소별 2024-03~06 월 중앙값
keys = sorted({k for x in meals[:2000] for k in x["ntr"]})
bym = C.defaultdict(lambda: C.defaultdict(list))
for x in meals:
    ym = x["ymd"][:6]
    if ym in ("202403", "202404", "202405", "202406", "202503", "202504"):
        for k, v in x["ntr"].items(): bym[k][ym].append(v)
        if x["kcal"] is not None: bym["열량"][ym].append(x["kcal"])
for k in keys + ["열량"]:
    print(f"{k:12s}", [(ym, round(st.median(v), 1)) for ym, v in sorted(bym[k].items())])
# 2. 같은 달(3~10월)끼리 학년도 비교 + 낸 학교 수
same = [x for x in meals if 3 <= x["m"] <= 10]
n_sy = C.Counter(x["sy"] for x in same)
schools_sy = {sy: {x["code"] for x in same if x["sy"] == sy} for sy in (2024, 2025, 2026)}
print("\n3~10월 끼니", dict(n_sy), "학교", {k: len(v) for k, v in schools_sy.items()})
for name, pat in T.items():
    r = [round(100 * sum(has(x, pat) for x in same if x["sy"] == sy) / n_sy[sy], 2) for sy in (2024, 2025, 2026)]
    sc = [len({x["code"] for x in same if x["sy"] == sy and has(x, pat)}) for sy in (2024, 2025, 2026)]
    print(f"  {name:10s} 끼니% {r}  낸 학교 {sc}")
# 3. 두바이 계열 월별
for lab, pat in (("두바이초콜릿류", r"두바이(?!쫀)"), ("두쫀쿠", r"두쫀쿠|두바이쫀")):
    ym = C.Counter(x["ymd"][:6] for x in meals if has(x, pat))
    print(lab, sorted(ym.items()))
# 4. 과일 분산 분해 (분석 스크립트 사전)
FR = G["과일"]
byc = C.defaultdict(lambda: [0, 0])
for x in meals:
    byc[x["code"]][1] += 1
    if has(x, FR): byc[x["code"]][0] += 1
rate = {c: 100 * a / b for c, (a, b) in byc.items() if b >= 100}
v = list(rate.values()); gm = st.mean(v)
grp = C.defaultdict(list)
for c, r in rate.items(): grp[SCH[c]["sigun"]].append(r)
ssb = sum(len(L) * (st.mean(L) - gm) ** 2 for L in grp.values()); sst = sum((r - gm) ** 2 for r in v)
k, n = len(grp), len(v)
print(f"\n과일(학교 {n}): 평균 {gm:.1f} 표준편차 {st.pstdev(v):.1f} 범위 {min(v):.1f}~{max(v):.1f}; 시군 설명 {100*ssb/sst:.1f}% (우연 기대 {100*(k-1)/(n-1):.1f}%)")
qs = sorted(v); print("  학교 사분위", round(qs[n//4],1), round(st.median(qs),1), round(qs[3*n//4],1))
# 무작위로 학교를 시군에 섞었을 때 설명 비율 분포
import random
random.seed(20261117)
labels = [SCH[c]["sigun"] for c in rate]; vals = list(rate.values()); sims = []
for _ in range(500):
    random.shuffle(labels)
    g = C.defaultdict(list)
    for l, r in zip(labels, vals): g[l].append(r)
    sims.append(sum(len(L) * (st.mean(L) - gm) ** 2 for L in g.values()) / sst)
print(f"  섞기 500번: 평균 {100*st.mean(sims):.1f}%, 상위 5% {100*sorted(sims)[475]:.1f}%, 실제보다 큰 경우 {sum(s >= ssb/sst for s in sims)}")
print("  2024 0끼 학교 설립연도 확인용:", [(SCH[c]["name"], SCH[c].get("fond", SCH[c].get("FOND_YMD"))) for c in list(SCH)[:1]])
