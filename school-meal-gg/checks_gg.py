"""전수 분석 결과 검증: 빠진 학교, 특징 메뉴의 학교 수, 열량·칼슘 이상값의 쏠림, 시군 차이 vs 학교 차이."""
import json, re, glob, collections as C, statistics as st
FORCE_RAW = True  # 진단은 특이값 처리 전 원본으로 한다
exec(open("analyze_gg.py").read().split("N = len(meals)")[0])  # 불러오기·정제 부분만 재사용
N = len(meals)
def has(meal, pat):
    return any(re.search(pat, d) for d in meal["dishes"])
codes_all = set(SCH)
codes_have = {x["code"] for x in meals}
print("자료 없는 학교:", [(SCH[c]["name"], SCH[c]["sigun"], SCH[c]["hs_type"]) for c in codes_all - codes_have])

# 학교당 학년도별 끼니 수
per = C.Counter((x["code"], x["sy"]) for x in meals)
for sy in (2024, 2025, 2026):
    v = sorted(per[(c, sy)] for c in codes_have)
    print(f"{sy}학년도 학교당 끼니: 최소 {v[0]} 하위10% {v[len(v)//10]} 중앙 {st.median(v)} 최대 {v[-1]}, 0끼 학교 {sum(a==0 for a in v)}")

# 특징 메뉴의 학교 수
feat = {"달밤라떼":10, "식목일케이크":4, "두쫀쿠":4, "상하이버터떡":5, "초코쌀뻥":4, "마시는샐러드":4, "요거얌얌":4, "레드향":1, "빼빼로":11, "오메기떡":12, "활짝핀떡갈비":4}
for d, m in feat.items():
    s = {x["code"] for x in meals if d in x["dishes"]}
    sm = {x["code"] for x in meals if d in x["dishes"] and x["m"] == m}
    sig = {SCH[c]["sigun"] for c in s}
    print(f"  {d}: 전체 {len(s)}개교({len(sig)}개 시군), {m}월에 낸 학교 {len(sm)}")

# 커피
cof = C.Counter(d for x in meals for d in x["dishes"] if re.search("커피|아메리카노|카페라떼|에스프레소|모카|카푸치노|디카페인", d))
print("커피 이름 요리:", cof.most_common(10), "끼니 수", sum(has(x, "커피|아메리카노|에스프레소|카푸치노|디카페인") for x in meals))

# 열량 이상값
kc = [(x["kcal"], x["code"], x["ymd"]) for x in meals if x["kcal"] is not None]
big = sorted(kc, reverse=True)[:8]
print("열량 상위:", [(k, SCH[c]["name"], y) for k, c, y in big])
for t in (1500, 2000, 5000):
    hit = [c for k, c, _ in kc if k > t]
    print(f"  열량>{t}: {len(hit)}끼, {len(set(hit))}개교")
low = [c for k, c, _ in kc if k < 300]
print(f"  열량<300: {len(low)}끼, {len(set(low))}개교", C.Counter(SCH[c]['name'] for c in low).most_common(3))

# 칼슘 이상값: 학교 쏠림
ca = C.defaultdict(list)
for x in meals:
    if "칼슘(mg)" in x["ntr"]:
        ca[x["code"]].append(x["ntr"]["칼슘(mg)"])
share = sorted(((sum(v > 1020 for v in L) / len(L), c) for c, L in ca.items()), reverse=True)
print("칼슘>1020 끼니가 있는 학교", sum(s > 0 for s, _ in share), "/", len(share))
print("  학교별 비율 상위:", [(round(100*s,1), SCH[c]["name"]) for s, c in share[:6]])
tot = sum(sum(v > 1020 for v in L) for L in ca.values())
top10 = sum(sum(v > 1020 for v in ca[c]) for _, c in share[:10])
print(f"  칼슘>1020 전체 {tot}끼 중 상위 10개교가 {top10} ({100*top10/tot:.0f}%)")
for y in ("2024", "2025", "2026"):
    L = [x["ntr"].get("칼슘(mg)", 0) for x in meals if x["ymd"][:4] == y]
    print(f"  {y}년 칼슘>1020 비율 {100*sum(v>1020 for v in L)/len(L):.1f}%")

# 과일: 시군 차이 vs 학교 차이 (분산 분해)
FR = r"수박|참외|귤|딸기|포도|사과|배$|복숭아|자두|키위|바나나|오렌지|파인애플|멜론|망고|감$|단감|연시|홍시|체리|블루베리|토마토|한라봉|레드향|천혜향|황금향|청포도|샤인|거봉|과일|후르츠|열대과일|석류|자몽"
sch_rate = {}
for c in codes_have:
    L = [x for x in meals if x["code"] == c] if False else None
byc = C.defaultdict(lambda: [0, 0])
for x in meals:
    byc[x["code"]][1] += 1
    if has(x, FR): byc[x["code"]][0] += 1
rate = {c: 100 * a / b for c, (a, b) in byc.items() if b >= 100}
allv = list(rate.values()); gm = st.mean(allv)
grp = C.defaultdict(list)
for c, v in rate.items(): grp[SCH[c]["sigun"]].append(v)
ssb = sum(len(v) * (st.mean(v) - gm) ** 2 for v in grp.values())
sst = sum((v - gm) ** 2 for v in allv)
print(f"과일 등장률(학교 단위): 평균 {gm:.1f}%, 최소 {min(allv):.1f} 최대 {max(allv):.1f}, 시군이 설명하는 분산 {100*ssb/sst:.1f}%")
for s in sorted(grp, key=lambda s: st.mean(grp[s])):
    v = grp[s]
    if s in ("포천시","안성시","하남시","구리시","가평군","연천군","과천시","수원시"):
        print(f"  {s}: 학교 {len(v)}, 평균 {st.mean(v):.1f}, 범위 {min(v):.1f}~{max(v):.1f}")

# 고유 요리 이름 수
print("고유 요리 이름:", len({d for x in meals for d in x["dishes"]}))
# 두쫀쿠·두바이 월별
for pat in ("두쫀쿠|두바이",):
    ym = C.Counter(x["ymd"][:6] for x in meals if has(x, pat))
    print(pat, sorted(ym.items())[-14:])

# 칼슘 월별 중앙값(언제 바뀌었나)
cm = C.defaultdict(list)
for x in meals:
    if "칼슘(mg)" in x["ntr"]: cm[x["ymd"][:6]].append(x["ntr"]["칼슘(mg)"])
print("칼슘 월별 중앙값·>1020 비율:", [(k, round(st.median(v)), round(100*sum(a>1020 for a in v)/len(v),1)) for k, v in sorted(cm.items())])
for y in ("2024", "2025"):
    L = [x for x in meals if x["ymd"][:4] == y and x["ntr"].get("칼슘(mg)", 0) > 1020]
    print(y, "고칼슘 끼니 중 우유 표기", round(100*sum(has(x, "우유") for x in L)/max(1,len(L)),1), "%", len(L))
zero24 = [SCH[c]["name"] for c in codes_have if per[(c, 2024)] == 0]
print("2024학년도 0끼 학교:", zero24)
