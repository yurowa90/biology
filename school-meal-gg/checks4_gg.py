import re, collections as C, statistics as st
src = open("analyze_gg.py").read()
exec(src.split("N = len(meals)")[0])
def has(meal, pat):
    return any(re.search(pat, d) for d in meal["dishes"])
cf = C.Counter(d for x in meals for d in x["dishes"] if re.search("커피|아메리카노|에스프레소|카푸치노|디카페인", d))
print("커피 낱말 요리:", cf.most_common())
mo = C.Counter(d for x in meals for d in x["dishes"] if "모카" in d)
print("모카 낱말 요리 수", sum(mo.values()), "중 이모카세", sum(v for k, v in mo.items() if "이모카세" in k))
lat = C.Counter(d for x in meals for d in x["dishes"] if "라떼" in d)
print("라떼 요리", sum(lat.values()), lat.most_common(8))
BOM = "냉이|달래|쑥|봄동|미나리|두릅|취나물|돌나물|원추리"
for m in (7, 8):
    c = C.Counter(re.search(BOM, d).group() for x in meals if x["m"] == m for d in x["dishes"] if re.search(BOM, d))
    print(m, "월 봄나물 낱말", c.most_common(5), C.Counter(d for x in meals if x["m"] == m for d in x["dishes"] if re.search(BOM, d)).most_common(5))
# 2024-03~04 칼슘: 학교별
sch = C.defaultdict(list)
for x in meals:
    if x["ymd"][:6] in ("202403", "202404") and "칼슘(mg)" in x["ntr"]:
        sch[x["code"]].append(x["ntr"]["칼슘(mg)"])
maj = [c for c, L in sch.items() if st.median(L) > 1020]
print("2024년 3~4월 기록 있는 학교", len(sch), "그중 칼슘 중앙값>1020", len(maj))
