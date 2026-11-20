"""경기도 고등학교 목록을 나이스 학교 코드와 대조한다(인증키 없이). 끊겨도 다시 실행하면 이어서 받는다.
입력: school_list_std.json (공공데이터포털 전국초중등학교위치표준데이터, README 참고)
출력: data/schools_neis.json (학교 ID → 나이스 코드, 고교 유형, 주소)
사용: python3 match_schools.py [동시요청수=8]
주의: 동명 학교 때문에 자동 대조가 안 된 2곳(예당고, 홍익디자인고)은 data/schools_neis.json에 손으로 넣어 두었다."""
import json, os, sys, time, datetime as dt, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

B = "https://open.neis.go.kr/hub/"
THREADS = int(sys.argv[1]) if len(sys.argv) > 1 else 8
os.makedirs("data", exist_ok=True)

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

# 1단계: 학교 코드
REGION = "경기도교육청"
frame = [x for x in json.load(open("school_list_std.json"))
         if x["SCHOOL_SE"] == "고등학교" and x["OPER_STTUS"] == "운영" and x["BNHH_SE"] == "본교"
         and x["CDDC_NM"] == REGION]
cache_f = "data/schools_neis.json"
cache = json.load(open(cache_f)) if os.path.exists(cache_f) else {}

def lookup(x):
    rows = get("schoolInfo", SCHUL_NM=x["SCHOOL_NM"])
    if rows is None:
        return x["SCHOOL_ID"], None  # 네트워크 실패: 다음 실행 때 다시
    rows = [r for r in rows if r["SCHUL_NM"] == x["SCHOOL_NM"]]
    if len(rows) > 1:
        key = " ".join(x["RDNMADR"].split()[1:3])
        rows = [r for r in rows if key and key in (r.get("ORG_RDNMA") or "")]
    if len(rows) != 1:
        return x["SCHOOL_ID"], {"match": "none", "name": x["SCHOOL_NM"], "cddc": x["CDDC_NM"]}
    r = rows[0]
    return x["SCHOOL_ID"], {"match": "ok", "ATPT": r["ATPT_OFCDC_SC_CODE"], "code": r["SD_SCHUL_CODE"],
                            "name": r["SCHUL_NM"], "cddc": x["CDDC_NM"], "addr": r["ORG_RDNMA"],
                            "hs_type": r.get("HS_SC_NM"), "fond": r.get("FOND_SC_NM"), "coedu": r.get("COEDU_SC_NM"),
                            "lat": x["LATITUDE"], "lon": x["LONGITUDE"]}

todo = [x for x in frame if x["SCHOOL_ID"] not in cache]
log("1단계 남은 학교", len(todo), "/", len(frame))
with ThreadPoolExecutor(THREADS) as ex:
    for n, (sid, v) in enumerate(ex.map(lookup, todo), 1):
        if v is not None:
            cache[sid] = v
        if n % 200 == 0:
            json.dump(cache, open(cache_f, "w"), ensure_ascii=False)
            log("1단계", n, "/", len(todo))
json.dump(cache, open(cache_f, "w"), ensure_ascii=False)
ok = [v for v in cache.values() if v.get("match") == "ok"]
log("1단계 끝: 코드 확인", len(ok), "이름 불일치", sum(v.get("match") == "none" for v in cache.values()))
