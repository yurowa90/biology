"""이상값 진단: 열량을 탄수화물·단백질·지방으로 다시 계산해(Atwater 4-4-9) 기록값과 견준다. 영양소별 로그 척도 MAD 진단."""
import re, collections as C, statistics as st, math
FORCE_RAW = True  # 진단은 특이값 처리 전 원본으로 한다
src = open("analyze_gg.py").read()
exec(src.split("N = len(meals)")[0])
N = len(meals)
K = ["탄수화물(g)", "단백질(g)", "지방(g)"]
ok = [x for x in meals if x["kcal"] is not None and all(k in x["ntr"] for k in K)]
print("열량·3대 영양소 모두 있는 끼니", len(ok), "/", N)
def atw(x):
    n = x["ntr"]; return 4 * n["탄수화물(g)"] + 4 * n["단백질(g)"] + 9 * n["지방(g)"]
ratio = [(x["kcal"] / atw(x) if atw(x) > 0 else float("inf")) for x in ok]
rs = sorted(r for r in ratio if math.isfinite(r))
print("기록열량/계산열량 비: 1%", round(rs[len(rs)//100], 3), "5%", round(rs[len(rs)//20], 3), "중앙", round(st.median(rs), 3), "95%", round(rs[19*len(rs)//20], 3), "99%", round(rs[99*len(rs)//100], 3))
for lo, hi in ((0.8, 1.25), (0.67, 1.5), (0.5, 2)):
    print(f"  비가 {lo}~{hi} 밖", sum(not (lo <= r <= hi) for r in ratio))
# 열량 큰 끼니: 계산값과 비교
big = sorted(ok, key=lambda x: -x["kcal"])[:12]
for x in big:
    print("  기록", x["kcal"], "계산", round(atw(x)), x["ntr"].get("탄수화물(g)"), x["ntr"].get("단백질(g)"), x["ntr"].get("지방(g)"), x["code"], x["ymd"], "요리", len(x["dishes"]))
small = sorted(ok, key=lambda x: x["kcal"])[:8]
for x in small:
    print("  작은", x["kcal"], "계산", round(atw(x)), x["code"], x["ymd"], x["dishes"][:5])
# 0 값과 결측
print("열량 결측", sum(x["kcal"] is None for x in meals), "열량 0", sum(x["kcal"] == 0 for x in meals))
for k in ["탄수화물(g)","단백질(g)","지방(g)","비타민A(R.E)","티아민(mg)","리보플라빈(mg)","비타민C(mg)","칼슘(mg)","철분(mg)"]:
    v = [x["ntr"][k] for x in meals if k in x["ntr"]]
    z = sum(a == 0 for a in v)
    pos = [math.log(a) for a in v if a > 0]
    med = st.median(pos); mad = st.median([abs(a - med) for a in pos]) * 1.4826
    hi = sum((a - med) / mad > 3.5 for a in pos); lo = sum((a - med) / mad < -3.5 for a in pos)
    print(f"{k:12s} n={len(v)} 0값={z} 로그MAD 위>{3.5}: {hi} 아래: {lo}  중앙 {math.exp(med):.1f}  위 경계 {math.exp(med+3.5*mad):.1f} 아래 경계 {math.exp(med-3.5*mad):.2f}")
# 요리 수 분포, 중복 날짜, 주말
nd = C.Counter(len(x["dishes"]) for x in meals)
print("끼니당 요리 수", sorted(nd.items())[:12])
dup = C.Counter((x["code"], x["ymd"]) for x in meals)
print("같은 학교 같은 날 중복", sum(v > 1 for v in dup.values()))
import datetime as dt
wk = sum(dt.date(int(x["ymd"][:4]), int(x["ymd"][4:6]), int(x["ymd"][6:])).weekday() >= 5 for x in meals)
print("주말 급식", wk)
one = [x for x in meals if len(x["dishes"]) <= 2]
print("요리 2개 이하 끼니 예", [x["dishes"] for x in one[:15]])
