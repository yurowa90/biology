"""「급식실의 1년」(activities/school-lunch-year.html)이 쓸 메뉴 은행을 만든다.
출력: ../activities/lunch-bank.js (window.LUNCH_BANK = {...})
사용: python3 build_lunch_bank.py [식약처 음식 영양성분 CSV 경로]

메뉴 고르기
- 아래 MENU에 사람이 고른 메뉴만 싣는다. 모두 경기도 고등학교 급식 자료(meal-lab-data.js)에 실제로 나온 이름이다.
- 이름이 자료에 없거나, 원본 급식 문자열에서 알레르기 표시를 찾지 못한 메뉴는 싣지 않는다(빠진 목록을 화면에 출력).

메뉴마다 담는 값
- a  : 알레르기 번호(1~19) 가운데 원본 급식 문자열(raw)의 그 메뉴 표시 절반 이상에 붙은 번호. 20 이상은 학교별 임의 번호라 뺀다.
- p  : 표시의 20% 이상 50% 미만에 붙은 번호(학교·레시피에 따라 들어감 → 게임에서 '레시피 확인' 경고)
- ag : [가장 흔한 표시와 같은 수, 전체 표시 수] — 학교마다 레시피가 달라 표시도 다를 수 있음을 보여 준다.
- f  : 10% 표본에서 그 이름이 나온 끼니 수, mo: 평소보다 자주 나오는 달(학기 중 달만, 표본 비율이 연중 평균의 1.8배 이상, 8끼 이상)
- m  : 조리법(이름 규칙), raw: 날로 먹는 채소·과일 여부, sh: 조개류(18) 포함 → 85℃ 가열 확인
- c  : 식재료비 단계 1~3(수업용 가정, 단가 자료 아님)
- nut: 식약처 「전국통합식품영양성분정보(음식)표준데이터」 값(1인분). CSV를 주면 채운다. 못 찾으면 null(지어내지 않음).

근거
- 알레르기 유발물질 19종: 식품 등의 표시·광고에 관한 법률 시행규칙 [별표 2](2024. 12. 30. 개정) Ⅰ.1.가
- 영양관리기준·식단 작성 고려사항: 학교급식법 시행규칙 [별표 3](2021. 1. 29. 개정), 제5조제2항
"""
import sys, io, json, re, csv, statistics, collections as C

DATA_JS = "../activities/meal-lab-data.js"
OUT_JS = "../activities/lunch-bank.js"

ALLERGENS = ["난류", "우유", "메밀", "땅콩", "대두", "밀", "고등어", "게", "새우", "돼지고기", "복숭아",
             "토마토", "아황산류", "호두", "닭고기", "쇠고기", "오징어", "조개류(굴·전복·홍합 포함)", "잣"]

# (이름, 칸, 식재료비 단계, 태그)  태그: 매움 전통 세계 계기:<날> 소화 보양 동해 채식
MENU = [
    # 밥
    ("쌀밥", "밥", 1, ""), ("혼합잡곡밥", "밥", 1, ""), ("흑미밥", "밥", 1, ""), ("보리밥", "밥", 1, ""),
    ("현미밥", "밥", 1, ""), ("찹쌀밥", "밥", 1, "소화"), ("카레라이스", "밥", 2, "세계"),
    ("마파두부덮밥", "밥", 2, "세계 매움"), ("짜장밥", "밥", 2, "세계"), ("흰죽", "밥", 1, "소화"),
    ("영양닭죽", "밥", 2, "소화 보양"),
    # 국·찌개
    ("쇠고기미역국", "국", 3, "전통"), ("들깨미역국", "국", 1, "전통 채식"), ("콩나물국", "국", 1, "소화 채식"),
    ("근대된장국", "국", 1, "전통"), ("미소된장국", "국", 1, "세계"), ("쇠고기무국", "국", 3, "소화"),
    ("순두부찌개", "국", 2, "매움"), ("된장찌개", "국", 1, "전통"), ("부대찌개", "국", 2, "매움"),
    ("육개장", "국", 3, "매움 전통"), ("어묵국", "국", 1, ""), ("오징어무국", "국", 2, "동해"),
    ("닭곰탕", "국", 2, "보양 소화"), ("조랭이떡국", "국", 2, "전통"), ("짬뽕국", "국", 2, "세계 매움"),
    ("마라탕", "국", 2, "세계 매움"), ("쌀국수", "국", 2, "세계"), ("닭다리삼계탕", "국", 3, "보양 전통 계기:초복"),
    ("홍합탕", "국", 2, ""), ("바지락미역국", "국", 2, ""), ("냉이된장국", "국", 1, "전통 제철:3.4"),
    # 주찬
    ("제육볶음", "주찬", 2, "매움"), ("돼지갈비찜", "주찬", 3, "전통"), ("안동찜닭", "주찬", 2, "전통"),
    ("닭갈비", "주찬", 2, "매움"), ("오리불고기", "주찬", 3, "보양"), ("마파두부", "주찬", 1, "세계 매움"),
    ("두부조림", "주찬", 1, "전통 채식"), ("계란찜", "주찬", 1, "소화"), ("계란말이", "주찬", 1, ""),
    ("삼치데리야끼구이", "주찬", 2, "세계"), ("고등어구이", "주찬", 2, "전통"), ("고등어무조림", "주찬", 2, "전통"),
    ("연어스테이크", "주찬", 3, "세계"), ("오삼불고기", "주찬", 2, "매움 동해"), ("오징어초무침", "주찬", 2, "동해"),
    ("오징어튀김", "주찬", 2, "동해"), ("탕수육", "주찬", 2, "세계"), ("꿔바로우", "주찬", 2, "세계"),
    ("돈육메추리알장조림", "주찬", 2, "전통"), ("함박스테이크", "주찬", 2, "세계"), ("치즈돈까스", "주찬", 2, "세계"),
    ("한우불고기", "주찬", 3, "전통"), ("수육", "주찬", 3, "전통"), ("탄두리치킨", "주찬", 2, "세계"),
    ("치킨퀘사디아", "주찬", 2, "세계"), ("코다리강정", "주찬", 2, ""), ("소시지야채볶음", "주찬", 2, ""),
    ("투움바파스타", "주찬", 2, "세계"),
    # 부찬
    ("콩나물무침", "부찬", 1, "채식"), ("잡채", "부찬", 2, "전통"), ("김구이", "부찬", 1, "채식"),
    ("시금치나물", "부찬", 1, "채식 전통 제철:12.1.2"), ("무말랭이무침", "부찬", 1, "채식 전통"), ("숙주나물무침", "부찬", 1, "채식"),
    ("미역줄기볶음", "부찬", 1, "채식"), ("양배추샐러드", "부찬", 1, "채식"), ("탕평채", "부찬", 2, "전통"),
    ("청포묵김가루무침", "부찬", 1, "채식 전통"), ("도토리묵무침", "부찬", 1, "채식 전통"), ("감자채볶음", "부찬", 1, "채식"),
    ("도라지오이생채", "부찬", 1, "채식 전통"), ("무생채", "부찬", 1, "채식 제철:10.11.12"), ("오이부추무침", "부찬", 1, "채식"),
    ("알감자조림", "부찬", 1, "채식"), ("꽈리고추멸치볶음", "부찬", 1, ""), ("견과류멸치볶음", "부찬", 2, ""),
    ("진미채볶음", "부찬", 2, "동해"), ("해물파전", "부찬", 2, "전통"), ("메밀전병", "부찬", 2, "전통"),
    ("국물떡볶이", "부찬", 1, "매움"), ("시금치프리타타", "부찬", 2, "세계"), ("브로콜리초회", "부찬", 1, "채식"),
    ("나쵸샐러드", "부찬", 2, "세계"), ("달래오이무침", "부찬", 1, "채식 제철:3.4"), ("오징어김치전", "부찬", 2, "동해"),
    ("감자채전", "부찬", 1, "채식"), ("고구마맛탕", "부찬", 1, "채식 제철:9.10.11"), ("연근조림", "부찬", 1, "채식 전통 제철:10.11.12"),
    # 김치
    ("배추김치", "김치", 1, "전통"), ("깍두기", "김치", 1, "전통"), ("총각김치", "김치", 1, "전통"),
    ("백김치", "김치", 1, "전통 소화"), ("열무김치", "김치", 1, "전통"), ("배추겉절이", "김치", 1, "전통"),
    ("단무지무침", "김치", 1, "세계"), ("오이피클", "김치", 1, "세계 채식"), ("오이김치", "김치", 1, "전통"),
    # 후식·음료
    ("사과", "후식", 1, "채식 과일 제철:9.10.11"), ("귤", "후식", 1, "채식 과일 제철:11.12.1.2"), ("바나나", "후식", 1, "채식 과일 소화"), ("수박", "후식", 2, "채식 과일 제철:6.7.8"),
    ("방울토마토", "후식", 1, "채식 과일"), ("파인애플", "후식", 1, "채식 과일"), ("요구르트", "후식", 1, "소화"),
    ("식혜", "후식", 1, "전통"),
    # 우유급식(식판 밖 따로): 우유 알레르기 학생에게는 두유가 대체식
    ("우유", "우유", 1, ""), ("두유", "우유", 1, "채식"),
    ("독도케이크", "후식", 2, "계기:독도"), ("크림찹쌀떡", "후식", 2, "계기:수능"), ("동지팥죽", "후식", 1, "전통 계기:동지 채식"),
    ("마카롱", "후식", 2, "세계"), ("에그타르트", "후식", 2, "세계"), ("열대과일샐러드", "후식", 2, "세계 채식"),
    ("수박화채", "후식", 2, "채식 과일 제철:6.7.8"), ("과일샐러드", "후식", 1, "과일"),
]

FRIED = r"튀김|까스|가스|커틀릿|강정|탕수|꿔바로우|너겟|후라이드|프라이드|맛탕"
METHOD = [("튀김", FRIED), ("국물", r"국$|탕$|찌개|국수|떡국|스프|수프|개장"), ("밥", r"밥$|라이스|죽$|덮밥"),
          ("전", r"전$|파전|부침|전병"), ("구이", r"구이|스테이크|김구이|치킨$|퀘사디아|말이|프리타타"),
          ("볶음", r"볶음|불고기|닭갈비|잡채|파스타|떡볶이|마파"), ("찜", r"찜$|찜닭|수육"), ("조림", r"조림|장조림"),
          ("무침", r"무침|생채|샐러드|겉절이|초회|탕평채|나물|피클|김치|깍두기|단무지"), ("기타", r".")]
RAW = r"생채|샐러드|겉절이|오이.*무침|달래.*무침|부추무침|무생채|피클"
FRUIT = {"사과", "귤", "바나나", "수박", "방울토마토", "파인애플", "열대과일샐러드", "수박화채", "과일샐러드"}
# 알레르기 표시가 이 수보다 적은 메뉴는 번호를 확정하지 않고 모두 '일부 학교에서만 표시'(p)로 둔다
FEW_LABELS = 5
# 이름만으로 주재료가 확실한 번호는 표시가 적어도 확정한다(우유·요구르트=2 우유, 두유=5 대두)
KNOWN = {"우유": {2}, "요구르트": {2}, "두유": {5}, "두부조림": {5}, "계란찜": {1}, "계란말이": {1}}
ANIMAL = {7, 8, 9, 10, 15, 16, 17, 18}  # 고등어·게·새우·돼지고기·닭고기·쇠고기·오징어·조개류
# 원자료 이상값: 같은 음식의 다른 행·원재료와 비교해 믿기 어려운 값은 빼고(null) 근거를 VERIFICATION 9절에 적는다
OUTLIER = {("마라탕", "b1"): "외식 분석 행 D306-278000000-0002 티아민 1.271 mg/100 g(돼지고기 살코기 수준)",
           ("잡채", "b1"): "가정식 분석 행 D110-492000000-0001 티아민 1.015 mg/100 g"}


def method(n, slot):
    if slot in ("후식", "김치"):
        return slot
    for m, pat in METHOD:
        if re.search(pat, n):
            return m


def load_meal_data():
    s = open(DATA_JS, encoding="utf-8").read()
    s = s[s.index("{"): s.rindex("}") + 1]
    return json.loads(s)


def allergy_labels(raw):
    lab = C.defaultdict(C.Counter)
    for r in raw:
        for part in re.split(r"<br\s*/?>", r[2]):
            part = part.strip().lstrip("-").strip()
            m = re.match(r"^(.*?)\s*\(([\d.\s]+)\)\s*$", part)
            name = re.sub(r"\(.*?\)|\[.*?\]|[*#@]|\s", "", m.group(1) if m else part)
            codes = tuple(sorted({int(x) for x in re.findall(r"\d+", m.group(2)) if 1 <= int(x) <= 19})) if m else ()
            lab[name][codes] += 1
    return lab


def months(sample, idx):
    tot = C.Counter(int(str(r[1])[4:6]) for r in sample)
    per = C.defaultdict(C.Counter)
    for r in sample:
        mo = int(str(r[1])[4:6])
        for i in r[4]:
            per[i][mo] += 1
    out = {}
    for i, cm in per.items():
        n = sum(cm.values())
        out[i] = sorted(mo for mo, k in cm.items() if tot[mo] >= 1000 and k >= 8 and (k / tot[mo]) >= 1.8 * (n / len(sample)))
    return out


# 식약처 「전국통합식품영양성분정보(음식)표준데이터」: 값은 100 g(또는 100 mL)당, 식품중량이 1인분 중량
# 같은 이름이 여러 출처로 있으면 학교급식에 가까운 출처부터 고른다(업체 제공 프랜차이즈 값은 쓰지 않음)
ORIGINS = ["중고등학교급식", "초등학교급식", "산업체급식", "가정식", "외식(분석", "외식(재료량"]
SCHOOL = ORIGINS[:3]  # 재료량 기반 1인분 중량이 학교·단체급식 기준인 출처
# 경기도 메뉴 이름 → 식약처 식품명(같은 음식, 이름만 다름). 검토 근거는 VERIFICATION.md 9절
ALIAS = {"쇠고기미역국": "소고기 미역국", "들깨미역국": "미역국_들깨", "쇠고기무국": "소고기 무국", "오징어무국": "오징어국",
         "조랭이떡국": "떡국_소고기", "닭다리삼계탕": "삼계탕", "홍합탕": "홍합국(홍합탕)", "안동찜닭": "닭찜", "닭갈비": "닭볶음(닭갈비)",
         "계란찜": "달걀찜", "계란말이": "달걀말이", "삼치데리야끼구이": "삼치구이", "고등어무조림": "고등어조림_무",
         "오징어초무침": "오징어무침_채소", "돈육메추리알장조림": "메추리알 돼지고기장조림", "한우불고기": "소불고기",
         "수육": "제육(돼지고기 수육)", "김구이": "조미 김구이", "숙주나물무침": "숙주나물", "청포묵김가루무침": "청포묵무침",
         "감자채볶음": "감자볶음", "도라지오이생채": "도라지생채_오이", "알감자조림": "감자조림", "꽈리고추멸치볶음": "꽈리고추볶음_잔멸치",
         "견과류멸치볶음": "멸치볶음_견과류", "진미채볶음": "오징어채볶음", "메밀전병": "빙떡(메밀전병)", "국물떡볶이": "떡볶이",
         "시금치프리타타": "오믈렛", "브로콜리초회": "브로콜리무침", "달래오이무침": "오이무침_달래", "오징어김치전": "김치전_오징어",
         "독도케이크": "케이크_생크림케이크", "크림찹쌀떡": "찹쌀떡_팥", "동지팥죽": "팥죽", "영양닭죽": "닭죽"}
# 이름은 있으나 같은 음식으로 보기 어렵거나 1인분 중량을 정할 수 없어 대응하지 않는 것
# (면이 든 짬뽕 ↔ 짬뽕국, 반찬 마파두부 ↔ 덮밥, 크림 스파게티 ↔ 투움바, 생오징어채볶음 ↔ 진미채, 마카롱·빙떡은 1인분 중량 불명)
NO_MATCH = {"짬뽕국", "마파두부덮밥", "투움바파스타", "순두부찌개", "마카롱", "메밀전병", "진미채볶음"}
# 1인분 중량을 자료에서 정할 수 없어 수업용으로 정한 것(한 조각)
PORTION = {"독도케이크": 50, "크림찹쌀떡": 50}
# 흰밥·잡곡밥은 1인분 양을 하나로 통일: 식약처 중고등학교급식 '~밥'(볶음·덮밥 제외) 1인분의 중앙값.
# 원자료는 쌀밥 450, 보리밥 280 mL처럼 달라서, 열량 차이가 곡물이 아니라 양에서 생겼음(VERIFICATION 9절)
RICE = {"쌀밥", "혼합잡곡밥", "흑미밥", "보리밥", "현미밥"}
# 음식 자료에 없는 우유·과일: 「원재료성식품」 표준데이터(15100065)의 식품명과 1인 1회 분량
# 과일 100 g: 식품군별 1인 1회 분량(과일류 약 50 kcal: 사과·배·바나나·포도·귤 100 g)
# 우유 200 mL: 학교 우유급식 1팩(수업용 가정, 1 mL ≈ 1 g으로 계산). 수박은 기준을 찾지 못해 다른 과일처럼 100 g
RAW_FOOD = {"사과": ("사과_생것", 100, "g"), "귤": ("귤_온주밀감_생것", 100, "g"), "바나나": ("바나나_생것", 100, "g"),
            "수박": ("수박_적육질_생것", 100, "g"), "방울토마토": ("토마토_방울토마토_생것", 100, "g"),
            "파인애플": ("파인애플_생것", 100, "g"), "우유": ("우유", 200, "mL")}
SERVING_NOTE = {"g": "과일 1인 1회 분량", "mL": "학교 우유 1팩(수업용 가정)"}
# 가공식품 표준데이터(15100066)에서 고를 것: 메뉴 → 대표식품명. 1회 분량은 같은 대표식품 제품들의 식품중량 중앙값
PROC_FOOD = {"두유": "두유", "요구르트": "농후발효유"}  # 식품공전 분류상 학교 급식의 요구르트는 농후발효유
NUT_COLS = {"kcal": "에너지(kcal)", "pro": "단백질(g)", "fat": "지방(g)", "cho": "탄수화물(g)", "sug": "당류(g)",
            "ca": "칼슘(mg)", "fe": "철(mg)", "na": "나트륨(mg)", "va": "비타민 A(μg RAE)", "b1": "티아민(mg)",
            "b2": "리보플라빈(mg)", "vc": "비타민 C(mg)"}


def num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def origin_rank(r):
    o = r.get("식품기원명", "")
    return next((i for i, k in enumerate(ORIGINS) if o.startswith(k)), None)


def load_nut(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "cp949"):
        try:
            text = raw.decode(enc); break
        except UnicodeDecodeError:
            continue
    rows = [r for r in csv.DictReader(io.StringIO(text)) if origin_rank(r) is not None]
    norm = lambda s: re.sub(r"[\s_()]", "", s or "")
    by = C.defaultdict(list)
    for r in rows:
        by[norm(r["식품명"])].append(r)
    # 학교급식 1인분 중량: 같은 식품대분류의 중고등·초등학교급식 메뉴 중량 중앙값
    med = C.defaultdict(list)
    for r in rows:
        if r["식품기원명"].startswith(("중고등학교급식", "초등학교급식")) and num(re.sub(r"[^\d.]", "", r["식품중량"])):
            med[r["식품대분류명"]].append(num(re.sub(r"[^\d.]", "", r["식품중량"])))
    med = {k: statistics.median(v) for k, v in med.items()}
    rice = [num(re.sub(r"[^\d.]", "", r["식품중량"])) for r in rows if r["식품기원명"].startswith("중고등학교급식")
            and r["식품대분류명"] == "밥류" and r["식품명"].endswith("밥") and not re.search(r"볶음|덮", r["식품명"])]
    med["__rice__"] = statistics.median([w for w in rice if w])
    return by, norm, rows, med


def read_csv(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "cp949"):
        try:
            return list(csv.DictReader(io.StringIO(raw.decode(enc))))
        except UnicodeDecodeError:
            continue


def nut_row(r, w, wu, wsrc, org):
    f = w / 100
    out = {k: (round(num(r.get(col)) * f, 2) if num(r.get(col)) is not None else None) for k, col in NUT_COLS.items()}
    out.update({"src": r["식품명"], "org": org, "w": w, "wu": wu, "wsrc": wsrc, "code": r["식품코드"],
                "date": r.get("데이터생성일자", ""), "ref": r.get("데이터기준일자", "")})
    return out


def proc_index(rows):
    """가공식품 표준데이터: 같은 대표식품 제품들의 100 g(mL)당 값과 식품중량의 중앙값으로 '보통 제품' 하나를 만든다(특정 상표를 고르지 않음)"""
    out = {}
    for name, rep in PROC_FOOD.items():
        c = [r for r in rows if r.get("대표식품명") == rep and num(re.sub(r"[^\d.]", "", r.get("식품중량") or ""))]
        if not c:
            continue
        med = lambda col: (statistics.median(v) if (v := [num(r.get(col)) for r in c if num(r.get(col)) is not None]) else None)
        w = round(statistics.median(num(re.sub(r"[^\d.]", "", r["식품중량"])) for r in c), 1)
        wu = "mL" if sum(r.get("영양성분함량기준량", "").lower().endswith("ml") for r in c) * 2 >= len(c) else "g"
        row = {col: med(col) for col in NUT_COLS.values()}
        row.update({"식품명": f"{rep}(제품 {len(c)}개 중앙값)", "식품코드": "", "데이터생성일자": max(r.get("데이터생성일자", "") for r in c),
                    "데이터기준일자": max(r.get("데이터기준일자", "") for r in c)})
        out[name] = nut_row(row, w, wu, f"같은 대표식품 제품 {len(c)}개의 식품중량 중앙값", "가공식품")
        nca = sum(1 for r in c if num(r.get(NUT_COLS["ca"])) is not None)
        out[name]["note"] = f"칼슘은 값을 적은 {nca}개 제품(주로 칼슘 강화 제품)의 중앙값이라 실제보다 높을 수 있어요. 제품 라벨을 확인하세요."
    return out


def nut_raw(name, raw_rows):
    """원재료성식품 표준데이터에서 우유·과일 값을 1인 1회 분량으로"""
    src, w, wu = RAW_FOOD[name]
    r = next((x for x in raw_rows if x["식품명"] == src), None)
    return r and nut_row(r, w, wu, SERVING_NOTE[wu], "원재료성식품(" + (r.get("출처명") or "")[:12] + ")")


def nut_of(name, by, norm, med):
    target = ALIAS.get(name, name)
    cands = by.get(norm(target)) or []
    if not cands or name in NO_MATCH:
        return None
    r = min(cands, key=origin_rank)
    w = num(re.sub(r"[^\d.]", "", r["식품중량"]))
    if name in PORTION:
        w, wsrc = PORTION[name], "수업용 가정(한 조각)"
    elif name in RICE:
        w, wsrc = med["__rice__"], "밥 1인분 통일(중고등학교급식 밥류 중앙값)"
    elif r["식품기원명"].startswith(tuple(SCHOOL)) and w:
        wsrc = "자료의 1인분"
    else:
        w, wsrc = round(med.get(r["식품대분류명"], statistics.median(list(med.values()))), 1), "같은 분류 학교급식 1인분 중앙값"
    return nut_row(r, w, "mL" if r.get("영양성분함량기준량", "").lower().endswith("ml") else "g", wsrc, r["식품기원명"])


def main():
    D = load_meal_data()
    dn, sample, raw = D["dn"], D["sample"], D["raw"]
    idx = {n: i for i, n in enumerate(dn)}
    cnt = C.Counter(i for r in sample for i in r[4])
    lab = allergy_labels(raw)
    mo = months(sample, idx)
    nut = None
    raw_rows = proc = None
    if len(sys.argv) > 1:
        by, norm, rows, med = load_nut(sys.argv[1])
        nut = (by, norm, med)
        print("식약처 CSV(업체 제공 제외)", len(rows), "행 · 밥 1인분 통일", med["__rice__"])
    if len(sys.argv) > 2:
        raw_rows = read_csv(sys.argv[2]); print("원재료성식품", len(raw_rows), "행")
    if len(sys.argv) > 3:
        proc = proc_index(read_csv(sys.argv[3]))
    menus, skipped, unmatched = [], [], []
    for name, slot, cost, tags in MENU:
        if name not in idx:
            skipped.append((name, "자료에 이름 없음")); continue
        if name not in lab:
            skipped.append((name, "알레르기 표시 없음")); continue
        (_, k), = lab[name].most_common(1)
        n_lab = sum(lab[name].values())
        share = C.Counter()
        for cs, c in lab[name].items():
            for x in cs:
                share[x] += c
        codes = sorted(x for x, c in share.items() if c / n_lab >= 0.5)
        maybe = sorted(x for x, c in share.items() if 0.2 <= c / n_lab < 0.5)
        few = n_lab < FEW_LABELS
        if few:  # 표시가 적으면 한 학교의 레시피일 수 있어 확정하지 않는다
            maybe, codes = sorted(set(codes) | set(maybe) | {x for x in share}), []
        if name in KNOWN:
            codes = sorted(set(codes) | KNOWN[name]); maybe = [x for x in maybe if x not in KNOWN[name]]
        tg = [t for t in tags.split() if t]
        if "채식" in tg and (set(codes) | set(maybe)) & ANIMAL:
            tg.remove("채식")  # 동물성 알레르기 번호가 있으면(일부 학교 포함) 채식 태그를 달지 않는다
        sm = [int(x) for t in tg if t.startswith("제철:") for x in t[3:].split(".")]
        item = {"n": name, "s": slot, "c": cost, "t": [t for t in tg if not t.startswith("제철:")], "sm": sm,
                "a": codes, "p": maybe, "ag": [k, n_lab], "few": few, "f": cnt[idx[name]], "mo": mo.get(idx[name], []),
                "m": method(name, slot), "raw": bool(re.search(RAW, name)) or name in FRUIT, "sh": 18 in codes, "nut": None}
        if nut:
            if name in RAW_FOOD:
                item["nut"] = nut_raw(name, raw_rows) if raw_rows else None
            elif name in PROC_FOOD:
                item["nut"] = proc.get(name) if proc else None
            else:
                item["nut"] = nut_of(name, *nut)
            for (on, k), why in OUTLIER.items():
                if on == name and item["nut"]:
                    item["nut"][k] = None; item["nut"].setdefault("drop", []).append(k)
            if not item["nut"]:
                unmatched.append(name); continue  # 영양값이 없는 메뉴는 싣지 않는다(지어내지 않음)
        menus.append(item)
    meta = {"built": __import__("datetime").date.today().isoformat(), "source": "경기도 고등학교 급식 10% 표본·원본 표본(NEIS), 식약처 전국통합식품영양성분정보 표준데이터: 음식(15100070)·원재료성식품(15100065)·가공식품(15100066)",
            # 데이터기준일자는 표준데이터 전체의 기준일, 데이터생성일자는 행마다 다름(고른 행 중 가장 늦은 날)
            "nutRefDate": max((m["nut"]["ref"] for m in menus if m["nut"]), default=None),
            "nutRowLatest": max((m["nut"]["date"] for m in menus if m["nut"]), default=None),
            "menus": len(menus), "withNut": sum(1 for m in menus if m["nut"]), "rawMeals": len(raw), "sampleMeals": len(sample)}
    js = "/* 자동 생성 파일: school-meal-gg/build_lunch_bank.py. 손으로 고치지 말 것 */\nwindow.LUNCH_BANK=" + json.dumps(
        {"meta": meta, "allergens": ALLERGENS, "menus": menus}, ensure_ascii=False, separators=(",", ":")) + ";\n"
    open(OUT_JS, "w", encoding="utf-8").write(js)
    by_slot = C.Counter(m["s"] for m in menus)
    print("실음", len(menus), dict(by_slot), "| 영양값 있음", meta["withNut"])
    for n, why in skipped:
        print("뺌:", n, "-", why)
    if unmatched:
        print("식약처 값 없음 → 뺌(" + str(len(unmatched)) + "):", ", ".join(unmatched))
    for m in menus:
        if m["nut"] and (m["n"] in ALIAS or m["nut"]["wsrc"] != "자료의 1인분"):
            n = m["nut"]; print(f"  대응 {m['n']} → {n['src']} [{n['org'][:8]}] {n['w']}g({n['wsrc']}) {n['kcal']} kcal")


if __name__ == "__main__":
    main()
