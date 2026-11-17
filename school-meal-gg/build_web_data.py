"""수업용 웹앱(activities/meal-lab.html)이 읽을 데이터 파일을 만든다.
출력: ../activities/meal-lab-data.js (window.MEAL_DATA = {...})  ← 경로는 인자로 바꿀 수 있다
사용: python3 build_web_data.py [출력 경로]

담는 것
- sample : 특이값 처리 후 끼니의 10% 단순 무작위 표본(씨앗 20261117). 차트 빌더와 재료 분류 사전이 쓴다.
- raw    : 정제 미션용 원본 표본(처리 전). 무작위 1,200끼 + 오류로 판정된 끼니 일부를 섞는다.
- schools: 학교별 요약(전수, 처리 후). '우리 학교' 비교에 쓴다.
- full   : 전수 집계표(제철, 특징 메뉴, 학년도 추이, 칼슘 월별, 처리 전후).
"""
import sys, json, re, random, statistics as st, collections as C, csv, math

src = open("analyze_gg.py").read()
exec(src.split("N = len(meals)")[0])  # 불러오기 + 특이값 처리(meals=처리 후, raw_meals=처리 전)
_g = src.split("GROUP = ")[1]; exec("GROUP = " + _g[:_g.index("}\n") + 1])
_s = src.split("SEASON = ")[1]; exec("SEASON = " + _s[:_s.index("}\n") + 1])
OUT_JS = sys.argv[1] if len(sys.argv) > 1 else "../activities/meal-lab-data.js"
rng = random.Random(20261117)

def has(meal, pat):
    return any(re.search(pat, d) for d in meal["dishes"])

# 학교·시군·유형 사전
codes = sorted({x["code"] for x in meals}, key=lambda c: (SCH[c]["sigun"], SCH[c]["name"]))
sigs = sorted({SCH[c]["sigun"] for c in codes})
types = sorted({SCH[c]["hs_type"] for c in codes})
ci = {c: i for i, c in enumerate(codes)}

# 학교별 요약(전수, 처리 후)
by = C.defaultdict(list)
for x in meals:
    by[x["code"]].append(x)
schools = []
for c in codes:
    ms = by[c]
    k = [x["kcal"] for x in ms if x["kcal"]]
    ca = [x["ntr"]["칼슘(mg)"] for x in ms if "칼슘(mg)" in x["ntr"]]
    uniq = len({d for x in ms for d in x["dishes"]})
    fr = 100 * sum(has(x, GROUP["과일"]) for x in ms) / len(ms)
    fi = 100 * sum(has(x, GROUP["생선·해산물"]) for x in ms) / len(ms)
    schools.append([SCH[c]["name"], sigs.index(SCH[c]["sigun"]), types.index(SCH[c]["hs_type"]), len(ms),
                    round(st.median(k)) if k else None, round(st.median(ca)) if ca else None,
                    round(uniq / len(ms), 2), round(fr, 1), round(fi, 1)])

# 10% 표본(처리 후)
samp = [x for x in meals if rng.random() < 0.10]
names = C.Counter(d for x in samp for d in x["dishes"])
dn = [d for d, _ in names.most_common()]
di = {d: i for i, d in enumerate(dn)}
sample = [[ci[x["code"]], int(x["ymd"]), round(x["kcal"]) if x["kcal"] else None,
           round(x["ntr"]["칼슘(mg)"]) if "칼슘(mg)" in x["ntr"] else None,
           [di[d] for d in x["dishes"]]] for x in samp]

# 정제 미션용 원본 표본(처리 전 문자열 그대로)
rawrec = {(r["SD_SCHUL_CODE"], r["MLSV_YMD"]): r for r in rows}
log = list(csv.DictReader(open("out/outlier_log.csv", encoding="utf-8-sig")))
bad = sorted({(r["학교 코드"], r["날짜"]) for r in log if r["규칙"][:2] in ("R1", "R2", "R4", "R8")})
pick = set(rng.sample(sorted(rawrec), 1200)) | set(rng.sample(bad, 60))
raw = []
for key in sorted(pick):
    r = rawrec.get(key)
    if not r or key[0] not in ci:
        continue
    kc = float(r["CAL_INFO"].split()[0]) if r.get("CAL_INFO") else None
    nt = {k: float(v) for k, v in re.findall(r"([^<>:]+?)\s*:\s*([\d\.]+)", r.get("NTR_INFO") or "")}
    raw.append([ci[key[0]], int(key[1]), r["DDISH_NM"], kc,
                nt.get("탄수화물(g)"), nt.get("단백질(g)"), nt.get("지방(g)")])
rng.shuffle(raw)

# 전수 집계표
def readcsv(name):
    return list(csv.reader(open(f"out/{name}.csv", encoding="utf-8-sig")))
full = {
    "season": readcsv("season_items"),
    "featured": readcsv("month_featured_dishes"),
    "trend": readcsv("trend_by_school_year"),
    "groups": readcsv("food_groups_monthly"),
    "cleanVsRaw": readcsv("clean_vs_raw"),
    "outlierSummary": readcsv("outlier_summary"),
    "calcium": json.load(open("out/chart_calcium_rows.json")),
}
mcount = C.Counter(x["m"] for x in meals)

data = {
    "meta": {"built": "2026-11-17", "meals": len(meals), "rawMeals": len(raw_meals), "schools": len(codes),
             "period": "2024-03-04 ~ 2026-11-13", "sampleRate": 0.10, "sampleN": len(sample), "seed": 20261117,
             "monthMeals": {str(m): mcount[m] for m in range(1, 13)}},
    "sigun": sigs, "types": types, "schools": schools, "dn": dn, "sample": sample, "raw": raw,
    "groups": GROUP, "season": SEASON, "full": full,
}
js = "/* 자동 생성 파일: school-meal-gg/build_web_data.py. 손으로 고치지 말 것 */\nwindow.MEAL_DATA=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
open(OUT_JS, "w").write(js)
print("쓴 파일", OUT_JS, f"{len(js.encode())/1e6:.2f}MB", "표본", len(sample), "고유 이름", len(dn), "원본 표본", len(raw), "학교", len(schools))
