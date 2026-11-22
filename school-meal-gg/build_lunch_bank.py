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
import sys, json, re, csv, collections as C

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
    ("홍합탕", "국", 2, ""), ("바지락미역국", "국", 2, ""), ("냉이된장국", "국", 1, "전통"),
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
    ("시금치나물", "부찬", 1, "채식 전통"), ("무말랭이무침", "부찬", 1, "채식 전통"), ("숙주나물무침", "부찬", 1, "채식"),
    ("미역줄기볶음", "부찬", 1, "채식"), ("양배추샐러드", "부찬", 1, "채식"), ("탕평채", "부찬", 2, "전통"),
    ("청포묵김가루무침", "부찬", 1, "채식 전통"), ("도토리묵무침", "부찬", 1, "채식 전통"), ("감자채볶음", "부찬", 1, "채식"),
    ("도라지오이생채", "부찬", 1, "채식 전통"), ("무생채", "부찬", 1, "채식"), ("오이부추무침", "부찬", 1, "채식"),
    ("알감자조림", "부찬", 1, "채식"), ("꽈리고추멸치볶음", "부찬", 1, ""), ("견과류멸치볶음", "부찬", 2, ""),
    ("진미채볶음", "부찬", 2, "동해"), ("해물파전", "부찬", 2, "전통"), ("메밀전병", "부찬", 2, "전통"),
    ("국물떡볶이", "부찬", 1, "매움"), ("시금치프리타타", "부찬", 2, "세계"), ("브로콜리초회", "부찬", 1, "채식"),
    ("나쵸샐러드", "부찬", 2, "세계"), ("달래오이무침", "부찬", 1, "채식"), ("오징어김치전", "부찬", 2, "동해"),
    ("감자채전", "부찬", 1, "채식"),
    # 김치
    ("배추김치", "김치", 1, "전통"), ("깍두기", "김치", 1, "전통"), ("총각김치", "김치", 1, "전통"),
    ("백김치", "김치", 1, "전통 소화"), ("열무김치", "김치", 1, "전통"), ("배추겉절이", "김치", 1, "전통"),
    ("단무지무침", "김치", 1, "세계"), ("오이피클", "김치", 1, "세계 채식"),
    # 후식·음료
    ("사과", "후식", 1, "채식"), ("귤", "후식", 1, "채식"), ("바나나", "후식", 1, "채식 소화"), ("수박", "후식", 2, "채식"),
    ("방울토마토", "후식", 1, "채식"), ("파인애플", "후식", 1, "채식"), ("요구르트", "후식", 1, "소화"),
    ("우유", "후식", 1, ""), ("두유", "후식", 1, "채식"), ("식혜", "후식", 1, "전통"),
    ("독도케이크", "후식", 2, "계기:독도"), ("크림찹쌀떡", "후식", 2, "계기:수능"), ("동지팥죽", "후식", 1, "전통 계기:동지 채식"),
    ("마카롱", "후식", 2, "세계"), ("에그타르트", "후식", 2, "세계"), ("열대과일샐러드", "후식", 2, "세계 채식"),
]

FRIED = r"튀김|까스|가스|커틀릿|강정|탕수|꿔바로우|너겟|후라이드|프라이드"
METHOD = [("튀김", FRIED), ("국물", r"국$|탕$|찌개|국수|떡국|스프|수프|개장"), ("밥", r"밥$|라이스|죽$|덮밥"),
          ("전", r"전$|파전|부침|전병"), ("구이", r"구이|스테이크|김구이|치킨$|퀘사디아|말이|프리타타"),
          ("볶음", r"볶음|불고기|닭갈비|잡채|파스타|떡볶이|마파"), ("찜", r"찜$|찜닭|수육"), ("조림", r"조림|장조림"),
          ("무침", r"무침|생채|샐러드|겉절이|초회|탕평채|나물|피클|김치|깍두기|단무지"), ("기타", r".")]
RAW = r"생채|샐러드|겉절이|오이.*무침|달래.*무침|부추무침|무생채|피클"
FRUIT = {"사과", "귤", "바나나", "수박", "방울토마토", "파인애플", "열대과일샐러드"}


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


# 식약처 CSV: 이름이 같은 것 → 정규화(공백·괄호 제거) → 수동 대응표 순서로 찾는다
ALIAS = {}  # 예: "혼합잡곡밥": "잡곡밥" — CSV를 받은 뒤 검토해 채운다
NUT_COLS = {"kcal": "에너지(kcal)", "pro": "단백질(g)", "fat": "지방(g)", "cho": "탄수화물(g)", "sug": "당류(g)",
            "ca": "칼슘(mg)", "fe": "철(mg)", "na": "나트륨(mg)", "va": "비타민 A(μg RAE)", "b1": "티아민(mg)",
            "b2": "리보플라빈(mg)", "vc": "비타민 C(mg)"}


def load_nut(path):
    for enc in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            rows = list(csv.DictReader(open(path, encoding=enc)))
            break
        except UnicodeDecodeError:
            continue
    norm = lambda s: re.sub(r"\(.*?\)|\s|_", "", s or "")
    by = {}
    for r in rows:
        nm = r.get("식품명", "")
        by.setdefault(nm, r)
        by.setdefault(norm(nm), r)
    return by, norm, rows


def num(v):
    try:
        return round(float(str(v).replace(",", "")), 2)
    except (TypeError, ValueError):
        return None


def main():
    D = load_meal_data()
    dn, sample, raw = D["dn"], D["sample"], D["raw"]
    idx = {n: i for i, n in enumerate(dn)}
    cnt = C.Counter(i for r in sample for i in r[4])
    lab = allergy_labels(raw)
    mo = months(sample, idx)
    nut = None
    if len(sys.argv) > 1:
        by, norm, rows = load_nut(sys.argv[1])
        nut = (by, norm)
        print("식약처 CSV", len(rows), "행")
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
        item = {"n": name, "s": slot, "c": cost, "t": [t for t in tags.split() if t],
                "a": codes, "p": maybe, "ag": [k, n_lab], "f": cnt[idx[name]], "mo": mo.get(idx[name], []),
                "m": method(name, slot), "raw": bool(re.search(RAW, name)) or name in FRUIT, "sh": 18 in codes, "nut": None}
        if nut:
            by, norm = nut
            r = by.get(name) or by.get(norm(name)) or by.get(ALIAS.get(name, "\0"))
            if r:
                item["nut"] = {k2: num(r.get(col)) for k2, col in NUT_COLS.items()}
                item["nut"]["src"] = r.get("식품명")
                item["nut"]["base"] = r.get("영양성분함량기준량") or r.get("영양성분함량 기준량")
                item["nut"]["serv"] = r.get("1인(회)분량 참고량")
                item["nut"]["wt"] = r.get("식품중량")
            else:
                unmatched.append(name)
        menus.append(item)
    meta = {"built": __import__("datetime").date.today().isoformat(), "source": "경기도 고등학교 급식 10% 표본·원본 표본(NEIS), 식약처 음식 영양성분 표준데이터(15100070)",
            "menus": len(menus), "withNut": sum(1 for m in menus if m["nut"]), "rawMeals": len(raw), "sampleMeals": len(sample)}
    js = "/* 자동 생성 파일: school-meal-gg/build_lunch_bank.py. 손으로 고치지 말 것 */\nwindow.LUNCH_BANK=" + json.dumps(
        {"meta": meta, "allergens": ALLERGENS, "menus": menus}, ensure_ascii=False, separators=(",", ":")) + ";\n"
    open(OUT_JS, "w", encoding="utf-8").write(js)
    by_slot = C.Counter(m["s"] for m in menus)
    print("실음", len(menus), dict(by_slot), "| 영양값 있음", meta["withNut"])
    for n, why in skipped:
        print("뺌:", n, "-", why)
    if unmatched:
        print("식약처 값 못 찾음(" + str(len(unmatched)) + "):", ", ".join(unmatched))


if __name__ == "__main__":
    main()
