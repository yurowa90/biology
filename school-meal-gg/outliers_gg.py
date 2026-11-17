"""의미 없는 특이값(오류) 처리 규칙. analyze_gg.py가 불러 쓴다.

원칙(문헌):
- 특이값을 '오류', '흥미로운 값', '영향력 있는 값'으로 나누고, 오류만 고치거나 지운다. 처리 기준과 건수를 보고한다
  (Aguinis, Gottfredson & Joo, 2013).
- 선별(screening) → 진단(diagnosing) → 편집(editing)의 순서를 밟고, 처리 전후 결과를 함께 보고한다
  (Van den Broeck et al., 2005).
- 평균±표준편차 대신 중앙값±MAD를 쓴다(Leys et al., 2013). 영양소는 오른쪽으로 긴 분포라 로그 척도에서 계산하고,
  기준은 보수적으로 z=5로 잡는다(로그 정규라면 24만 끼 중 우연히 넘을 끼니가 1끼 미만인 거리).

원칙 적용:
- 끼니 기록 자체를 지우는 것은 '급식이 아닌 기록'(휴업일, 공휴일 안내 등)과 '밥 하나만 적힌 불완전 기록' 두 가지뿐이다.
- 영양 값이 틀린 끼니도 메뉴(요리 이름)는 남긴다. 틀린 값만 결측으로 바꾼다.
- 아래쪽 꼬리(낮은 비타민C 같은)는 실제로 있을 수 있어 0만 결측으로 본다.
"""
import math, re, statistics as st, collections as C

NUTRIENTS = ["탄수화물(g)", "단백질(g)", "지방(g)", "비타민A(R.E)", "티아민(mg)", "리보플라빈(mg)", "비타민C(mg)", "칼슘(mg)", "철분(mg)"]
Z = 5.0
# 급식이 아닌 안내 문구(모든 요리 칸이 이런 문구일 때만 해당). 대체식·간편식·파업 대체식은 실제로 나간 끼니라 남긴다.
NOMEAL = re.compile(r"휴업|공휴일|휴일|선거일|비급식|급식\s*없|미실시|(?<![가-힣])미급식|현충일|어린이날|성탄절|추석|설날|개천절|한글날|"
                    r"광복절|삼일절|제헌절|신정|석가탄신|부처님|개교기념일|체험학습|방학식|종업식|휴교|수고하셨습니다|국군의날")
RICE_ONLY = re.compile(r"^(추가|혼합|친환경|칼슘|발아|유기농|우리)?(잡곡|흑미|현미|찹쌀|보리|기장|차수수|수수|차조|조|쌀|백미|흰|귀리|검정쌀|흑찰|찰|콩|율무|녹미|오곡|칼슘|강화|Ca백미|백|흑)*밥([\s(\-].*|[A-Za-z]{0,2})?$")  # 흑미밥, 혼합잡곡밥(s, 흑미밥-동중 등 지은 밥만
CALCIUM_BAD_MONTHS = {"202403", "202404"}  # 칼슘만 평소의 4배 넘게 기록된 달(기록 방식 변화로 추정)


def _robust(values):
    lg = [math.log(v) for v in values if v and v > 0]
    med = st.median(lg)
    mad = 1.4826 * st.median([abs(a - med) for a in lg])
    return med, mad


def clean_meals(meals):
    """meals(analyze_gg 형식)를 받아 (정리된 meals, 처리 기록 행, 규칙별 요약 행)을 돌려준다."""
    log, cnt = [], C.Counter()

    def note(x, var, old, rule):
        log.append([x["code"], x["ymd"], var, old, rule]); cnt[rule] += 1

    def drop_nutrients(x, rule):
        note(x, "열량·영양소 전체", x["kcal"], rule)
        x["kcal"] = None; x["ntr"] = {}

    # R1. 급식이 아닌 기록 → 끼니 기록 삭제
    # R8. 요리가 밥 하나뿐인 기록(나머지 요리가 빠진 불완전 기록) → 끼니 삭제
    kept = []
    for x in meals:
        if not x["dishes"] or all(NOMEAL.search(d) for d in x["dishes"]):
            note(x, "끼니 기록", "/".join(x["dishes"]), "R1 급식이 아닌 기록(휴업·공휴일 안내 등) → 끼니 삭제")
        elif len(x["dishes"]) == 1 and RICE_ONLY.search(x["dishes"][0]):
            note(x, "끼니 기록", x["dishes"][0], "R8 요리가 밥 하나뿐인 불완전 기록 → 끼니 삭제")
        else:
            kept.append(x)
    meals = kept

    for x in meals:
        # R2. 영양 기록 없음(열량 0 또는 결측) → 영양 값 전체 결측
        if not x["kcal"]:
            if x["kcal"] == 0 or x["ntr"]:
                drop_nutrients(x, "R2 열량 0(기록 없음) → 영양 값 결측")
            continue
        n = x["ntr"]
        # R3. 3대 영양소로 다시 계산한 열량(4·4·9)과 1.5배 넘게 어긋남 → 영양 기록 전체를 믿을 수 없음
        if all(k in n for k in NUTRIENTS[:3]):
            atw = 4 * n["탄수화물(g)"] + 4 * n["단백질(g)"] + 9 * n["지방(g)"]
            if atw <= 0 or abs(math.log(x["kcal"] / atw)) > math.log(1.5):
                drop_nutrients(x, "R3 기록 열량과 3대 영양소 계산 열량 불일치(1.5배 초과) → 영양 값 결측")
                continue

    # R4. 열량 극단값(로그 중앙값±5 MAD 밖) → 재료량 입력 오류로 보고 영양 값 전체 결측
    med, mad = _robust([x["kcal"] for x in meals if x["kcal"]])
    lo, hi = math.exp(med - Z * mad), math.exp(med + Z * mad)
    for x in meals:
        if x["kcal"] and not (lo <= x["kcal"] <= hi):
            drop_nutrients(x, f"R4 열량 극단값({lo:.0f}~{hi:.0f}kcal 밖) → 영양 값 결측")

    for x in meals:
        n = x["ntr"]
        # R5. 칼슘 기록 방식이 바뀐 달 → 칼슘만 결측
        if x["ymd"][:6] in CALCIUM_BAD_MONTHS and "칼슘(mg)" in n:
            note(x, "칼슘(mg)", n.pop("칼슘(mg)"), "R5 2024년 3~4월 칼슘(기록 방식 변화) → 칼슘 결측")
        # R6. 열량은 있는데 영양소 하나가 정확히 0 → 그 영양소 결측(기록 누락)
        for k in NUTRIENTS:
            if k in n and n[k] == 0:
                note(x, k, n.pop(k), "R6 영양소 값 0(기록 누락) → 그 영양소 결측")

    # R7. 영양소별 위쪽 극단값(로그 중앙값+5 MAD 초과) → 그 영양소만 결측
    bounds = {}
    for k in NUTRIENTS:
        m, d = _robust([x["ntr"][k] for x in meals if k in x["ntr"]])
        bounds[k] = math.exp(m + Z * d)
        for x in meals:
            if k in x["ntr"] and x["ntr"][k] > bounds[k]:
                note(x, k, x["ntr"].pop(k), f"R7 {k} 극단값({bounds[k]:.1f} 초과) → 그 영양소 결측")

    summary = [[rule, c] for rule, c in sorted(cnt.items())]
    return meals, log, summary, {"kcal_bounds": (lo, hi), "nutrient_upper": bounds}
