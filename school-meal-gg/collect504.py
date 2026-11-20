"""경기도 고등학교 전수(나이스 코드가 확인된 504곳) 2024-03-04 ~ 2026-11-13 점심 수집. 끊기면 다시 실행해 이어 받는다.
입력: data/schools_neis.json (match_schools.py 결과)
출력: data/meals/<학교 코드>.json (학교별 원본), schools504.json
사용: python3 collect504.py [동시요청수=8]"""
import json, os, random, sys, time, datetime as dt, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

B = "https://open.neis.go.kr/hub/"
THREADS = int(sys.argv[1]) if len(sys.argv) > 1 else 8
START, END = dt.date(2024, 3, 4), dt.date(2026, 11, 13)
os.makedirs("data/meals", exist_ok=True)

def get(ep, **q):
    q.update(Type="json", pIndex=1, pSize=5)
    u = B + ep + "?" + urllib.parse.urlencode(q)
    for i in range(6):
        try:
            with urllib.request.urlopen(u, timeout=30) as r:
                d = json.load(r)
            return d[ep][1]["row"] if ep in d else []
        except Exception:
            time.sleep(2 + 3 * i)
    return None

def log(*a):
    print(time.strftime("%H:%M:%S"), *a, file=sys.stderr, flush=True)

def lunch(s, a, b):
    return get("mealServiceDietInfo", ATPT_OFCDC_SC_CODE=s["ATPT"], SD_SCHUL_CODE=s["code"],
               MMEAL_SC_CODE=2, MLSV_FROM_YMD=a, MLSV_TO_YMD=b)

# 1. 학교 목록(전수)
sample = [v for v in json.load(open("data/schools_neis.json")).values() if v.get("match") == "ok"]
for v in sample:
    v["sigun"] = v["addr"].split()[1]
json.dump(sample, open("schools504.json", "w"), ensure_ascii=False, indent=1)
log("학교", len(sample))

# 2. 점심 수집
weeks = []
d = START
while d <= END:
    weeks.append((d.strftime("%Y%m%d"), (d + dt.timedelta(days=4)).strftime("%Y%m%d")))
    d += dt.timedelta(days=7)

def school(s):
    f = f"data/meals/{s['code']}.json"
    if os.path.exists(f):
        return "skip"
    out = []
    for a, b in weeks:
        rows = lunch(s, a, b)
        if rows is None:
            return "fail"
        out += rows
    json.dump(out, open(f + ".tmp", "w"), ensure_ascii=False)
    os.replace(f + ".tmp", f)
    return len(out)

todo = [s for s in sample if not os.path.exists(f"data/meals/{s['code']}.json")]
log("수집 남은 학교", len(todo), "/", len(sample), "주", len(weeks))
t0 = time.time(); done = fail = 0
with ThreadPoolExecutor(THREADS) as ex:
    for r in ex.map(school, todo):
        done += 1; fail += r == "fail"
        if done % 10 == 0 or done == len(todo):
            rate = done / (time.time() - t0)
            log("수집", done, "/", len(todo), "실패", fail, f"남은 시간 약 {(len(todo) - done) / rate / 60:.0f}분")
log("수집 끝. 실패", fail, "(다시 실행하면 실패한 학교만 받음)")
