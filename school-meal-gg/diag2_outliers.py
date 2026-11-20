import re, collections as C, statistics as st, math
FORCE_RAW = True  # 진단은 특이값 처리 전 원본으로 한다
src = open("analyze_gg.py").read()
exec(src.split("N = len(meals)")[0])
# 1. 요리 3개 이하 끼니의 요리 이름
few = C.Counter(d for x in meals if len(x["dishes"]) <= 3 for d in x["dishes"])
print("요리 3개 이하 끼니의 이름 상위:", few.most_common(45))
# 2. 열량 로그 MAD 경계
kc = [x["kcal"] for x in meals if x["kcal"]]
lg = [math.log(a) for a in kc]; med = st.median(lg); mad = 1.4826 * st.median([abs(a - med) for a in lg])
for z in (3, 3.5, 5):
    print(f"열량 로그 MAD z={z}: {math.exp(med - z*mad):.0f} ~ {math.exp(med + z*mad):.0f} kcal, 밖 {sum(abs(a-med)/mad > z for a in lg)}")
# 3. 낮은 열량 끼니(<400) 내용
low = [x for x in meals if x["kcal"] and x["kcal"] < 400 and len(x["dishes"]) >= 4]
print("요리 4개 이상인데 400kcal 미만", len(low), C.Counter(x["code"] for x in low).most_common(5))
for x in low[:6]: print("  ", x["kcal"], x["ymd"], x["code"], x["dishes"])
bd = [x for x in meals if x["code"] == C.Counter(x["code"] for x in low).most_common(1)[0][0]]
v = sorted(x["kcal"] for x in bd if x["kcal"]); print("  그 학교 열량 분포", v[:3], st.median(v), v[-3:], "끼니", len(v), sorted(C.Counter(x["ymd"][:6] for x in bd if x["kcal"] and x["kcal"] < 400).items()))
# 4. 열량 정상(400~1500) 끼니에서 미량 영양소 최댓값
norm = [x for x in meals if x["kcal"] and 400 <= x["kcal"] <= 1500]
for k in ["비타민A(R.E)", "티아민(mg)", "리보플라빈(mg)", "비타민C(mg)", "칼슘(mg)", "철분(mg)"]:
    vv = sorted(((x["ntr"].get(k, 0), x) for x in norm if x["ymd"][:6] not in ("202403", "202404") or k != "칼슘(mg)"), key=lambda t: -t[0])
    print(k, "상위", [(round(a, 1), x["dishes"][:4]) for a, x in vv[:3]], "99.9%", round(sorted(a for a, _ in vv)[int(.999 * len(vv))], 1))
