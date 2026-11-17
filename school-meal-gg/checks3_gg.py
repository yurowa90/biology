"""8절 서술용 수치: 표기 다양성, 해안 시군 생선 비교, 3개 학년도 모두 기록 있는 학교 수."""
import re, collections as C, statistics as st, random
FORCE_RAW = True  # 진단은 특이값 처리 전 원본으로 한다
src = open("analyze_gg.py").read()
exec(src.split("N = len(meals)")[0])
def has(meal, pat):
    return any(re.search(pat, d) for d in meal["dishes"])
_g = src.split("GROUP = ")[1]; exec("G = " + _g[:_g.index("}\n") + 1])
raw = C.Counter(it.strip() for r in rows for it in r["DDISH_NM"].split("<br/>") if it.strip())
cl = C.Counter(d for x in meals for d in x["dishes"])
print("원문 표기", len(raw), "정제 후", len(cl), "한 번만 나온 정제 이름 비율", round(100*sum(v==1 for v in cl.values())/len(cl),1))
kim = [k for k in raw if "배추김치" in k]
print("배추김치 원문 변형", len(kim), "예", kim[:12])
print("정제 후 배추김치 끼니", sum(1 for x in meals if "배추김치" in x["dishes"]))
coast = {"안산시","시흥시","화성시","평택시","김포시"}
FISH = G["생선·해산물"]
rate = C.defaultdict(lambda:[0,0])
for x in meals:
    rate[x["code"]][1]+=1
    if has(x, FISH): rate[x["code"]][0]+=1
sr = {c:100*a/b for c,(a,b) in rate.items() if b>=100}
cv = [v for c,v in sr.items() if SCH[c]["sigun"] in coast]; iv = [v for c,v in sr.items() if SCH[c]["sigun"] not in coast]
d = st.mean(cv)-st.mean(iv)
labs = [SCH[c]["sigun"] in coast for c in sr]; vals=list(sr.values()); random.seed(20261117); cnt=0
for _ in range(2000):
    random.shuffle(labs); a=[v for l,v in zip(labs,vals) if l]; b=[v for l,v in zip(labs,vals) if not l]
    if abs(st.mean(a)-st.mean(b)) >= abs(d): cnt+=1
print(f"생선·해산물 학교 평균: 해안 5개 시군 {len(cv)}곳 {st.mean(cv):.1f}%, 나머지 {len(iv)}곳 {st.mean(iv):.1f}%, 차이 {d:+.1f}, 섞기 p≈{cnt/2000:.2f}")
per = C.Counter((x["code"], x["sy"]) for x in meals)
codes = {x["code"] for x in meals}
full = [c for c in codes if all(per[(c,sy)] > 0 for sy in (2024,2025,2026))]
print("3개 학년도 모두 기록", len(full), "/", len(codes))
print("요리 수/끼니 중앙값", st.median(len(x["dishes"]) for x in meals))
