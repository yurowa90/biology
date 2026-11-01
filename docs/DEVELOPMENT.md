# 개발 안내

사용자용 안내는 [README](../README.md)에 있습니다. 이 문서는 사이트를 고치거나 배포를 관리하는 사람을 위한 내용입니다.

## 파일 구성

서버(백엔드)가 없는 정적 파일입니다. 홈(`index.html`)이 사이트 루트로 배포되고, 활동은 `activities/` 아래에 둡니다.

```
index.html                                  교과서 홈(목차 네비게이션)
activities/enzyme-kinetics.html             효소반응속도 워크북(UI + 로직 + 시뮬레이터 + 서술형 자가 점검)
activities/enso.html                        엘니뇨·라니냐 워크북(시뮬레이터 + ONI·실시간 수온 + GRASPS 자가 점검·자기평가)
teacher.html                                교사 대시보드
data/oni.json                               NOAA ONI(배포 때 자동 수집, 저장소에는 오프라인용 스냅샷/자리표시)
scripts/fetch-oni.mjs                       NOAA ONI → data/oni.json 변환·검증, 활동 HTML 내장 스냅샷 교체(외부 의존성 없음)
.github/workflows/deploy-pages.yml          GitHub Pages 자동 배포(루트 경로) + 배포 시 ONI 수집 + 매주 재배포
.github/workflows/refresh-oni-snapshot.yml  (수동 실행) 저장소 스냅샷을 NOAA 최신값으로 커밋
.nojekyll                                   Pages의 Jekyll 처리 비활성화
```

## 배포 워크플로

- `deploy-pages.yml`은 `main`, `master`, `claude/bioscience-webapp-se292i` 브랜치에 푸시할 때와 매주 월요일 06:47(KST, 일요일 21:47 UTC)에 실행되며, 수동 실행(`workflow_dispatch`)도 됩니다.
- **Settings → Pages → Build and deployment → Source는 반드시 "GitHub Actions"** 여야 합니다. "Deploy from a branch"로 되어 있으면 푸시마다 브랜치 원본 빌드("pages build and deployment")가 이 워크플로 배포와 동시에 돌아, 늦게 끝난 쪽이 게시됩니다. 브랜치 원본이 이기면 자리표시 `data/oni.json`이 게시되어 화면에 "데이터 없음"이 뜹니다(활동은 정상 동작, 파일 불러오기 가능).
- Actions 없이 배포하려면 Source를 "Deploy from a branch", 폴더를 `/ (root)`로 지정합니다. 이 경우 ONI 자동 수집은 일어나지 않습니다.
- GitHub `schedule`은 **저장소 기본 브랜치**에 있는 워크플로 파일로만 실행됩니다. 이 저장소의 기본 브랜치는 현재 `claude/bioscience-webapp-se292i`입니다. 기본 브랜치를 `main`으로 바꾸면 이 워크플로 파일도 `main`에 있어야 주간 갱신이 돕니다. 공개 저장소에서 60일간 활동이 없으면 GitHub이 예약 실행을 자동으로 멈춥니다.
- API 키·비밀값은 쓰지 않습니다.

## ONI 자료 갱신

| 데이터 | 출처 | 방식 |
|--------|------|------|
| ONI(월별 3개월 이동평균 Niño3.4 편차) | NOAA CPC `oni.ascii.txt` | 빌드 시점 수집: 배포 워크플로가 `node scripts/fetch-oni.mjs --inject activities/enso.html`로 받아 `data/oni.json`과 페이지 내장 스냅샷을 채운 뒤 배포(커밋 없음). 매주 재배포 |
| 실시간 해수면 온도 | Open-Meteo Marine API(키 불필요) | 학생이 버튼을 누를 때만 브라우저에서 호출. 서태평양(0°, 150°E)과 Niño3.4 중심(0°, 145°W) |

페이지가 ONI를 찾는 순서: ① 같은 사이트의 `data/oni.json` → ② 페이지에 내장된 스냅샷 → ③ 둘 다 없으면 "데이터 없음"을 표시하고 NOAA `oni.ascii.txt`를 직접 불러오도록(파일 선택) 안내. 로컬(`file://`)에서는 ①을 건너뜁니다.

- 저장소의 `data/oni.json`은 현재 자리표시(pending)입니다. 작업 환경에서 NOAA 접속이 막혀 있어 실제 값을 넣지 않았고, 값을 지어내지도 않았습니다. 배포된 사이트에는 빌드 때 실제 값이 들어갑니다.
- 저장소 스냅샷도 채우려면 **Actions → Refresh ONI snapshot → Run workflow**를 한 번 실행하거나, 인터넷이 되는 PC에서 `node scripts/fetch-oni.mjs --inject activities/enso.html`을 실행해 커밋합니다.
- 수집에 실패해도 배포는 멈추지 않습니다(스크립트가 경고만 남기고 기존 파일 유지). 검증 조건: 600행 이상, 연도·계절·편차 범위 확인.

## 설계 원칙

활동 유형 6종과 설계 프레임워크의 대응: `개념`(지식구성 기초) · `시뮬레이션`(맥락·하이테크) · `PBL`(문제해결·프로젝트형) · `GRASPS`(수행과제) · `형성평가`(과정중심평가) · `성찰`(메타인지·하이터치).

설계 원리(연수: AI·디지털 기반 교육혁신 선도교사): ① 맥락(실생활 연결) ② 지식구성(능동 탐구·성찰) ③ 상호작용·협력(모둠·토론) ④ 맞춤교육(개별화·데이터). 하이터치(관계·정서·고차사고)와 하이테크(AI 진단·시각화·시뮬레이션·자동 피드백)의 균형, 그리고 진단(사전) → 형성평가·즉각 피드백 → 성찰(KWL) → 교사 대시보드(데이터·직관 균형)의 과정중심평가–성찰 연계를 지향합니다.

GRASPS 활동은 앞으로 만들 때 슬롯별로 따로 생성하지 않고 Role↔Audience↔Situation을 한 세트로 함께 만들며, Goal·Product는 거기서 파생하고 Standards는 마지막에 도출합니다. 청중 근접성 축으로 3개 번들을 나눕니다(홈의 GRASPS 카드에 메모).

활동 데이터에는 출처(`sources`) 필드가 있어 교차 참고한 출판사를 활동별로 기록할 수 있습니다(현재 비어 있음).

### 활동의 출발점

- 엘니뇨·라니냐 워크북은 연수 교안의 "Gemini 웹앱 시뮬레이터를 활용한 엘니뇨 탐구" 수업을 효소 워크북과 같은 8단계 구조로 옮기고 실제 관측 자료를 붙인 것입니다.
- 효소 워크북은 로켓방정식(치올콥스키 식) 학습 워크북을 생명과학 맥락으로 옮긴 것입니다. 대응 관계: 치올콥스키 식 유도 ↔ 미카엘리스–멘텐 식 유도 / 연소율 ṁ, 추력 `F = vₑ·ṁ` ↔ 회전수 kcat, `Vmax = kcat·[E]₀` / 지면·로켓 두 관점 시뮬레이터 ↔ 직접 곡선·이중역수 두 표현 + 억제제 효과.

## 자가 점검과 보고서 필드

- 효소 워크북 서술형 점검 항목
  - 서술 1: 낮은 [S]의 반응 차수 · 그 까닭(빈 활성 부위) · 높은 [S]의 속도·차수 · 효소 포화의 뜻 · 식(분모 근사) 근거 · Km의 의미
  - 서술 2: 경쟁적(결합 자리 · Km · Vmax · 높은 [S]로 극복) · 비경쟁적(결합 자리 · Vmax · Km) · 이중역수 그래프(경쟁적 / 비경쟁적의 절편·기울기). '경쟁적'과 '비경쟁적'을 다룬 부분을 나눠 점검해, 두 억제제의 변화를 뒤바꿔 쓰면 ✓가 나오지 않습니다.
  - 점검 항목마다 한국어·영어 표현(띄어쓰기 허용 정규식)을 둡니다.
- 엘니뇨 GRASPS 점검 항목: 공통 5항목(근거 수치·±0.5 ℃ 기준, 메커니즘(무역풍·용승·수온약층), 지역별 영향, 청중 맞춤 제안, 출처)에 과제별로 대기 순환·강수, 불확실성 항목이 더해집니다. '작성 틀 넣기' 문구는 점검과 글자 수에서 뺍니다.
- 보고서 payload: 엘니뇨 보고서는 `activityId: "enso"`. GRASPS 자기평가는 `grasps.review`, 예시 개요 열람은 `grasps.exemplarViewed`·`exemplarViewedAt`. 효소 서술형 예시 답안 열람은 `essayReview.<문항>.exemplarViewed / exemplarViewedAt / exemplarLenAtView`. 교사 대시보드는 예시답안 열람을 새 보고서부터 표시하며, 예전 보고서도 그대로 읽습니다. CSV에는 '예시답안 열람' 열이 들어갑니다.

## 고치는 곳

- 목차: `index.html`의 `CURRICULUM` 데이터(대단원 ▸ 중단원 ▸ 활동), 활동 유형은 `TYPE`, 활동 객체의 `sources`(출처) 필드
- 효소 워크북 문항: `activities/enzyme-kinetics.html`의 `PREDICT`, `CHECK`, `QUIZ`, `ESSAY`, `DERIV` 배열
- 효소 서술형 자가 점검·예시 답안: `ESSAY_RUBRIC`(점검 항목·안내 질문·정규식), `EXEMPLAR`(모범답안), `MIN_EXEMPLAR_LEN`(기본 60자)
- 엘니뇨 GRASPS 루브릭: `GRASPS_CHECKS`, 기준별 연결은 `BUNDLES[].standards[].checks`, 예시 개요는 `GRASPS_EXEMPLAR`
- 제출 방식: 각 활동 파일 상단의 `CONFIG.submit`
- 프롬프트 복사 버튼 숨기기: 각 활동 파일 상단 `CONFIG.showPromptCopy = false`
- 디자인 토큰: `<style>`의 `:root` CSS 변수
- 시뮬레이터 파라미터 범위: `S_MAX`, 슬라이더 `min/max`, `computeApparent()`(억제 모델)
