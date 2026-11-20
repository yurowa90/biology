"""경기도 고등학교 전수 급식 분석(2024학년도~2026학년도 점심). 교육자료(에듀넷) 주제별로 데이터 질문 하나씩.
출력: 화면 요약 + out/*.csv (수업 도구에 실을 집계표, 특이값 처리 후). --raw로 실행하면 처리 전 집계를 out_raw/에 쓴다."""
import json, re, csv, os, sys, collections as C, statistics as st

import glob
SCH = {v["code"]: v for v in json.load(open("data/schools_neis.json")).values() if v.get("match") == "ok"}
for v in SCH.values():
    v["sigun"] = v["addr"].split()[1]
rows = []
for f in glob.glob("data/meals/*.json"):
    for r in json.load(open(f)):
        sc = SCH.get(r["SD_SCHUL_CODE"])
        if sc:
            r["stratum"] = sc["sigun"]; r["hs_type"] = sc["hs_type"]; rows.append(r)
sample = SCH
ORDER = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2]
MLAB = {m: f"{m}월" for m in ORDER}

def clean(s):
    s = re.sub(r"\([\d\.,\s]*\)", "", s)
    s = re.sub(r"[\*\#\@◆★☆♥♡]", "", s)
    s = re.sub(r"\(\s*(자율|선택|sm|SM|중고등|완|구|중|고)\s*\)|\[\s*(자율|선택)\s*\]", "", s)
    s = re.sub(r"\s+", "", s).strip("-/.,&+")
    s = re.sub(r"(?<=[가-힣\)])[A-Za-z]{1,3}$", "", s)  # 학교마다 붙인 영문 표시(h, J, k 등)
    return s

def allergens(s):
    return {int(x) for g in re.findall(r"\(([\d\.,\s]+)\)", s) for x in re.findall(r"\d+", g) if 1 <= int(x) <= 19}

meals = []  # 끼니 단위
for r in rows:
    items = [it for it in r["DDISH_NM"].split("<br/>") if it.strip()]
    meals.append({
        "code": r["SD_SCHUL_CODE"], "stratum": r["stratum"], "ymd": r["MLSV_YMD"],
        "m": int(r["MLSV_YMD"][4:6]), "hs_type": r["hs_type"],
        "sy": int(r["MLSV_YMD"][:4]) - (1 if int(r["MLSV_YMD"][4:6]) < 3 else 0),
        "dishes": [clean(i) for i in items if clean(i)],
        "allergens": [allergens(i) for i in items if clean(i)],
        "kcal": float(r["CAL_INFO"].split()[0]) if r.get("CAL_INFO") else None,
        "ntr": {k: float(v) for k, v in re.findall(r"([^<>:]+?)\s*:\s*([\d\.]+)", r.get("NTR_INFO") or "")},
    })
# 의미 없는 특이값(오류) 처리. --raw로 실행하거나 FORCE_RAW=True로 불러 쓰면 원본 그대로 본다.
RAW = "--raw" in sys.argv or globals().get("FORCE_RAW", False)
OUT = "out_raw" if RAW else "out"
os.makedirs(OUT, exist_ok=True)
if not RAW:
    from outliers_gg import clean_meals, NUTRIENTS
    import copy, math as _m
    raw_meals = copy.deepcopy(meals)
    meals, OUTLOG, OUTSUM, OUTB = clean_meals(meals)
N = len(meals)
mc = C.Counter(x["m"] for x in meals)
print(f"끼니 {N}, 학교 {len({x['code'] for x in meals})}, 요리 {sum(len(x['dishes']) for x in meals)}")
print("월별 끼니", [mc[m] for m in ORDER])

def has(meal, pat):
    return any(re.search(pat, d) for d in meal["dishes"])

def monthly_rate(pat):
    hit = C.Counter(x["m"] for x in meals if has(x, pat))
    return [round(100 * hit[m] / mc[m], 1) if mc[m] else None for m in ORDER]

def write(name, header, data):
    with open(f"{OUT}/{name}.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(data)

# 1. 월별 특징 메뉴 (그 달 비중 / 연중 비중)
dish_all = C.Counter(d for x in meals for d in set(x["dishes"]))
bym = C.defaultdict(C.Counter)
for x in meals:
    for d in set(x["dishes"]):
        bym[x["m"]][d] += 1
feat = []
print("\n[월별 특징 메뉴]")
for m in ORDER:
    if mc[m] < 150: continue
    sc = [((c / mc[m]) / (dish_all[d] / N), d, c) for d, c in bym[m].items() if c >= 30 and dish_all[d] >= 60]
    top = sorted(sc, reverse=True)[:8]
    print(MLAB[m], [(d, round(l, 1)) for l, d, c in top])
    feat += [[MLAB[m], d, c, mc[m], round(l, 2)] for l, d, c in top]
write("month_featured_dishes", ["월", "메뉴", "그 달 등장 끼니", "그 달 끼니", "연중 대비 배율"], feat)
print("상위 15 (단순 빈도):", dish_all.most_common(15))

# 2. 제철 재료
SEASON = {"수박": "수박", "참외": "참외", "귤·감귤": "귤|감귤|한라봉|황금향|천혜향", "딸기(생과)": "^딸기$|^생딸기",
          "딸기(이름 포함 전체)": "딸기", "포도류": "포도|거봉|샤인", "봄나물": "냉이|달래|쑥|봄동|미나리|두릅|취나물|돌나물|원추리",
          "옥수수": "옥수수|콘", "고구마": "고구마", "단호박": "단호박"}
print("\n[제철 재료: 100끼당 등장 끼니 %]", [MLAB[m] for m in ORDER])
srows = []
for k, p in SEASON.items():
    v = monthly_rate(p); print(k.ljust(10), v); srows.append([k, p] + v)
write("season_items", ["재료", "규칙"] + [MLAB[m] for m in ORDER], srows)

# 3. 재료군 (식품 구성 자전거 묶음에 맞춤)
GROUP = {"곡류(밥 외 면·빵·떡)": "국수|우동|파스타|스파게티|면$|라면|짜장|짬뽕|냉면|쫄면|칼국수|빵|베이글|토스트|떡|또띠아|피자",
         "고기": "돈육|돼지|제육|삼겹|목살|수육|돈까스|돈가스|탕수육|보쌈|족발|닭|치킨|계육|소고기|쇠고기|불고기|갈비|우육|차돌|햄|소시지|베이컨|미트",
         "생선·해산물": "고등어|삼치|갈치|가자미|명태|동태|코다리|오징어|새우|주꾸미|쭈꾸미|낙지|조기|임연수|꽁치|연어|참치|어묵|해물|조개|홍합|바지락|굴",
         "달걀": "계란|달걀|에그|오믈렛|스크램블", "콩·두부": "두부|콩(?!나물)|된장|청국장|유부",
         "우유·유제품": "우유|요구르트|요거트|치즈|라떼|아이스크림", "과일": "|".join(["수박", "참외", "귤", "감귤", "사과", "배$", "포도", "딸기", "바나나", "오렌지", "파인애플", "멜론", "복숭아", "자두", "키위", "망고", "방울토마토", "샤인", "거봉", "한라봉", "황금향", "블루베리", "체리", "과일"]),
         "김치": "김치|깍두기|석박지|겉절이"}
print("\n[재료군: 끼니 중 등장 %]")
grows = []
for k, p in GROUP.items():
    v = monthly_rate(p); tot = round(100 * sum(has(x, p) for x in meals) / N, 1)
    print(k.ljust(12), tot, v); grows.append([k, tot] + v)
write("food_groups_monthly", ["재료군", "연중 %"] + [MLAB[m] for m in ORDER], grows)

# 3b. 지역별(층) 생선·해산물, 고기
print("\n[시군별 재료군 %]")
st_rows = []
strata = sorted({x["stratum"] for x in meals})
for s in strata:
    ms = [x for x in meals if x["stratum"] == s]
    vals = [round(100 * sum(has(x, GROUP[g]) for x in ms) / len(ms), 1) for g in ["생선·해산물", "고기", "과일", "우유·유제품"]]
    print(s.ljust(18), len(ms), vals); st_rows.append([s, len(ms)] + vals)
write("strata_food_groups", ["시군", "끼니", "생선·해산물 %", "고기 %", "과일 %", "우유·유제품 %"], st_rows)

# 4. 조리법 (자료: 부엌에서 만날 수 있는 화학 변화)
COOK = {"튀김": "튀김|까스|가스$|커틀릿|강정|탕수|프라이드|치킨|고로케|크로켓|너겟|핫도그", "구이": "구이|스테이크|바베큐|BBQ|오븐",
        "볶음": "볶음|볶이|덮밥|볶은", "찜": "찜$|찜닭|수육", "조림": "조림|장조림", "무침·생채": "무침|생채|겉절이|샐러드",
        "국·탕·찌개": "국$|탕$|찌개|전골|개장", "전·부침": "전$|부침|빈대떡|지짐", "발효 식품(빵·장류·요구르트·식혜)": "빵|요구르트|요거트|된장|청국장|식혜"}
print("\n[조리법: 끼니 중 등장 %]")
crow = []
for k, p in COOK.items():
    v = monthly_rate(p); tot = round(100 * sum(has(x, p) for x in meals) / N, 1)
    print(k.ljust(12), tot, v); crow.append([k, tot] + v)
write("cooking_methods_monthly", ["조리법", "연중 %"] + [MLAB[m] for m in ORDER], crow)

# 5. 세계 음식 (자료: 세계의 음식 문화)
WORLD = {"자료 속 4가지(타코·케밥·파에야·쌀국수)": "타코|케밥|케밥|파에야|빠에야|쌀국수", "중식": "짜장|짬뽕|탕수육|마파|깐풍|유린기|마라|꿔바로우|팔보채|양장피|딤섬|만두",
         "일식": "우동|돈부리|규동|가츠|카츠|소바|스시|초밥|오코노미|타코야키|라멘|미소", "서양식": "파스타|스파게티|피자|리조또|스테이크|그라탕|햄버거|버거|샌드위치|토스트",
         "동남아·인도": "쌀국수|팟타이|나시고렝|커리|카레|탄두리|분짜|월남쌈|똠얌|반미", "멕시코": "타코|부리또|브리또|퀘사디아|나쵸|나초|화이타", "마라": "마라"}
print("\n[세계 음식: 끼니 중 등장 %]")
wrow = []
for k, p in WORLD.items():
    v = monthly_rate(p); tot = round(100 * sum(has(x, p) for x in meals) / N, 1)
    print(k.ljust(20), tot, v); wrow.append([k, tot] + v)
write("world_food_monthly", ["음식 문화", "연중 %"] + [MLAB[m] for m in ORDER], wrow)

# 6. 음식 궁합 (자료: 음식 궁합) — 같은 끼니에 함께 나오는가. 건강 효과가 아니라 동시 출현만 본다.
RADISH = r"(?<!오)무(?!침)|깍두기|석박지"
PAIRS = [("고등어", RADISH), ("된장", "부추"), ("냉면", "식초"), ("새우", "표고"), ("닭", "인삼|삼계"),
         ("미역", "(?<![가-힣])파$|대파|쪽파|파채|파무침"), ("(?<!튀)김$|김구이|김자반|김가루", "기름|참기름|들기름"), (RADISH, "오이")]
print("\n[음식 궁합 동시 출현: A끼니, B끼니, 함께, 기대값 대비 배율]")
prow = []
for a, b in PAIRS:
    A = [has(x, a) for x in meals]; Bv = [has(x, b) for x in meals]
    na, nb = sum(A), sum(Bv); nab = sum(1 for i in range(N) if A[i] and Bv[i])
    lift = round(nab / (na * nb / N), 2) if na and nb else None
    print(a, b, na, nb, nab, lift); prow.append([a, b, na, nb, nab, lift])
write("food_pairs", ["A 규칙", "B 규칙", "A 끼니", "B 끼니", "함께 나온 끼니", "기대값 대비 배율"], prow)

# 7. 영양 (자료: 영양소 과다 섭취) — 한 끼 값의 분포. 기준값은 아직 원문 대조 전.
print("\n[영양소: 한 끼 중앙값, 5~95백분위, 이상값 후보]")
keys = sorted({k for x in meals for k in x["ntr"]})
nrow = []
for k in keys:
    v = sorted(x["ntr"][k] for x in meals if k in x["ntr"])
    q = lambda p: v[min(len(v) - 1, int(p * len(v)))]
    med = st.median(v); out_hi = sum(1 for a in v if a > 4 * med)
    print(k.strip().ljust(14), len(v), round(med, 1), round(q(.05), 1), round(q(.95), 1), "4배 초과", out_hi)
    nrow.append([k.strip(), len(v), round(med, 1), round(q(.05), 1), round(q(.95), 1), out_hi])
kc = sorted(x["kcal"] for x in meals if x["kcal"])
print("열량", len(kc), st.median(kc), kc[0], kc[-1], ">1500:", sum(a > 1500 for a in kc), "<300:", sum(a < 300 for a in kc))
nrow.append(["열량(kcal)", len(kc), st.median(kc), round(kc[int(.05 * len(kc))], 1), round(kc[int(.95 * len(kc))], 1), sum(a > 1500 for a in kc)])
write("nutrients_per_meal", ["영양소", "끼니", "중앙값", "5백분위", "95백분위", "큰 값(중앙값의 4배 초과, 열량은 1,500kcal 초과)"], nrow)

# 학교별 중앙값 (우리 학교 대 전국 비교용)
srow = []
for c, s in sample.items():
    ms = [x for x in meals if x["code"] == c]
    if not ms: continue
    k2 = [x["kcal"] for x in ms if x["kcal"]]
    ca = [x["ntr"].get("칼슘(mg) ", x["ntr"].get("칼슘(mg)")) for x in ms]
    ca = [a for a in ca if a is not None]
    uniq = len({d for x in ms for d in x["dishes"]})
    srow.append([s["sigun"], s["name"], s["hs_type"], s["fond"], len(ms), round(st.median(k2), 1) if k2 else None,
                 round(st.median(ca), 1) if ca else None, uniq, round(uniq / len(ms), 2)])
write("school_summary", ["시군", "학교", "고교 유형", "설립", "끼니", "열량 중앙값", "칼슘 중앙값", "고유 메뉴 수", "끼니당 고유 메뉴"], srow)

# 8. 커피·카페인 (자료: 커피 2편)
print("\n[커피·카페인 관련 메뉴]", C.Counter(d for x in meals for d in x["dishes"] if re.search("커피|모카|티라미수|라떼|녹차|홍차|초코", d)).most_common(12))

# 9. 알레르기 (영양교육의 안전 측면)
AL = {1: "난류", 2: "우유", 3: "메밀", 4: "땅콩", 5: "대두", 6: "밀", 7: "고등어", 8: "게", 9: "새우", 10: "돼지고기", 11: "복숭아", 12: "토마토", 13: "아황산류", 14: "호두", 15: "닭고기", 16: "쇠고기", 17: "오징어", 18: "조개류", 19: "잣"}
tot_d = sum(len(x["dishes"]) for x in meals)
ac = C.Counter(a for x in meals for s in x["allergens"] for a in s)
arow = [[AL[k], k, round(100 * v / tot_d, 1)] for k, v in ac.most_common()]
safe = {}
for k in (2, 6, 1):
    safe[AL[k]] = st.median([sum(1 for s in x["allergens"] if k not in s) for x in meals])
print("\n[알레르기 표시 비율 %]", arow[:10], "\n한 끼에서 피해도 남는 요리 수 중앙값", safe)
write("allergens", ["알레르기 유발 식품", "번호", "요리 중 표시 %"], arow)

# 10. 학년도별 변화 (유행 메뉴)
TREND = {"마라": "마라", "탕후루": "탕후루", "두바이": "두바이", "약과": "약과", "로제": "로제", "버블티·흑당": "버블|흑당|타피오카",
         "요거트·그릭": "그릭|요거트볼", "쌀국수": "쌀국수", "샐러드": "샐러드", "제로·저당": "제로|저당|무가당"}
years = sorted({x["sy"] for x in meals})
ys = C.Counter(x["sy"] for x in meals)
print("\n[학년도별 유행 메뉴: 끼니 중 %]", years, [ys[y] for y in years])
trow = []
for k, p in TREND.items():
    v = [round(100 * sum(1 for x in meals if x["sy"] == y and has(x, p)) / ys[y], 2) for y in years]
    print(k.ljust(10), v); trow.append([k, p] + v)
write("trend_by_school_year", ["메뉴", "규칙"] + [f"{y}학년도" for y in years], trow)

# 11. 고교 유형별
print("\n[고교 유형별]")
hrow = []
for t in sorted({x["hs_type"] for x in meals}):
    ms = [x for x in meals if x["hs_type"] == t]
    k2 = [x["kcal"] for x in ms if x["kcal"]]
    vals = [round(100 * sum(has(x, GROUP[g]) for x in ms) / len(ms), 1) for g in ["생선·해산물", "고기", "과일", "우유·유제품"]]
    print(t, len({x["code"] for x in ms}), len(ms), round(st.median(k2), 1), vals)
    hrow.append([t, len({x["code"] for x in ms}), len(ms), round(st.median(k2), 1)] + vals)
write("hs_type_summary", ["고교 유형", "학교", "끼니", "열량 중앙값", "생선·해산물 %", "고기 %", "과일 %", "우유·유제품 %"], hrow)
# 12. 특이값 처리 기록과 처리 전후 비교 (자료: 정제 미션 F-06)
if not RAW:
    write("outlier_log", ["학교 코드", "날짜", "변수", "원래 값", "규칙"], OUTLOG)
    write("outlier_summary", ["규칙", "건수"], OUTSUM)
    print("\n[특이값 처리]", f"끼니 {len(raw_meals)} → {len(meals)}")
    for r in OUTSUM: print("  ", r[1], r[0])
    crow = []
    def _vals(ms, k):
        return [x["kcal"] for x in ms if x["kcal"]] if k == "열량(kcal)" else [x["ntr"][k] for x in ms if k in x["ntr"]]
    for k in ["열량(kcal)"] + NUTRIENTS:
        a, b = _vals(raw_meals, k), _vals(meals, k)
        crow.append([k, len(a), round(st.mean(a), 1), round(st.median(a), 1), round(max(a), 1),
                     len(b), round(st.mean(b), 1), round(st.median(b), 1), round(max(b), 1)])
        print("  ", k.ljust(12), "평균", crow[-1][2], "→", crow[-1][6], "| 중앙값", crow[-1][3], "→", crow[-1][7], "| 최댓값", crow[-1][4], "→", crow[-1][8])
    write("clean_vs_raw", ["변수", "처리 전 끼니", "처리 전 평균", "처리 전 중앙값", "처리 전 최댓값",
                           "처리 후 끼니", "처리 후 평균", "처리 후 중앙값", "처리 후 최댓값"], crow)
print("\n집계표:", sorted(os.listdir(OUT)))
