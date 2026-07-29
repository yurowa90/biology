# 효소반응속도 학습 워크북 · 미카엘리스–멘텐

로켓방정식(치올콥스키 식) 학습 워크북을 **생명과학 맥락**으로 옮긴 탐구형 웹앱입니다.
효소·물질대사 단원의 핵심 정량식인 **미카엘리스–멘텐 반응속도식**을 중심으로, 학생이
예측 → 유도 → 개념 → 시뮬레이션 → 평가 → 서술형 → 보고서까지 스스로 밟아 갑니다.

**서버(백엔드)가 필요 없는 단일 정적 파일**(`index.html`)이라, GitHub Pages에 그대로 올리면 됩니다.

## 8단계 흐름

| # | 단계 | 내용 |
|---|------|------|
| 01 | 예측 (PREDICT) | 채점하지 않는 직관 문항 — [S]를 높이면 v는? 효소 2배면 Vmax는? |
| 02 | 이론 유도 (THEORY) | E+S⇌ES→E+P 에서 정상상태 가정으로 `v = Vmax·[S]/(Km+[S])` 유도 (6단계 아코디언) |
| 03 | 회전수 kcat (TURNOVER) | `Vmax = kcat·[E]₀`, 촉매효율 kcat/Km, 낮은/높은 기질 농도에서의 거동 |
| 04 | 시뮬레이터 (SIMULATOR) | 효소 반응 애니메이션 + v–[S] 포화 곡선 ↔ 이중역수(Lineweaver–Burk) 그래프. Vmax·Km·[S]·억제제(경쟁적/비경쟁적) 슬라이더, 실시간 수치와 체크리스트 |
| 05 | 유도 확인 (CHECK) | 유도 각 단계를 확인하는 4지선다 4문항, 즉시 채점·해설 |
| 06 | 형성평가 (FORMATIVE) | 포화·효소농도·억제제·회전수 종합 4문항 |
| 07 | 서술형 · AI | 서술형 2문항 + **Claude API 직접 호출**로 즉석 피드백 |
| 08 | 최종 보고서 (SUBMIT) | 전체 답안·점수 정리 → 제출 / 인쇄(PDF) / 다운로드 |

원본 로켓 워크북과의 대응:

- 치올콥스키 식 유도 ↔ 미카엘리스–멘텐 식 유도
- 연소율 ṁ, 추력 `F = vₑ·ṁ` ↔ 회전수 kcat, `Vmax = kcat·[E]₀`
- 지면/로켓 두 관점 시뮬레이터 ↔ 직접 곡선 / 이중역수 두 표현 + 억제제 효과

## GitHub Pages 로 배포하기

### 방법 A — GitHub Actions (권장, 이미 설정됨)
저장소에 `.github/workflows/deploy-pages.yml` 이 포함되어 있습니다.

1. 저장소 → **Settings → Pages**
2. **Build and deployment → Source** 를 **“GitHub Actions”** 로 선택
3. 이 브랜치(`main`/`master` 또는 작업 브랜치)에 푸시하면 자동 배포됩니다.
   배포가 끝나면 `https://<사용자명>.github.io/<저장소명>/` 에서 열립니다.

### 방법 B — 브랜치에서 바로 배포 (Actions 없이)
1. 저장소 → **Settings → Pages**
2. **Source: Deploy from a branch** → 브랜치 선택, 폴더는 **`/ (root)`**
3. 저장하면 잠시 후 위와 같은 URL 로 게시됩니다. (`index.html` 이 루트에 있어 그대로 동작)

> 로컬에서 확인만 하려면 `index.html` 을 브라우저로 그냥 열어도 됩니다. 답안과 진행 상황은
> 브라우저 `localStorage` 에 저장됩니다.

## 제출 방식 (백엔드 불필요)

`index.html` 상단의 `CONFIG.submit.mode` 로 선택합니다. 기본값은 설정이 필요 없는 `"download"` 입니다.

| mode | 동작 | 설정 |
|------|------|------|
| `"download"` (기본) | 보고서를 JSON 파일로 저장 → 학생이 구글 클래스룸/이메일로 제출 | 없음 |
| `"googleForm"` | **구글 폼**으로 전송 → 연결된 스프레드시트에 자동 기록 (Apps Script 아님) | 폼 ID + 필드 매핑 |
| `"endpoint"` | Formspree / Cloudflare Worker 등 임의의 POST URL 로 전송 | URL 1개 |

**구글 폼으로 자동 수집하기** (스프레드시트에 쌓고 싶을 때, 서버 없이):
1. 구글 폼을 만들고 필요한 항목마다 **단답형** 질문을 추가합니다(모두 “필수 아님”).
   전체 답안을 통째로 저장하려면 `payload` 항목 하나만 있어도 됩니다.
2. 폼 미리보기에서 **페이지 소스 보기** → 각 질문의 `entry.XXXXXXX` 번호를 찾습니다.
3. `CONFIG.submit.mode = "googleForm"` 으로 바꾸고 `googleForm.formId` 와 `entries` 를 채웁니다.
   `formId` 는 폼 주소 `.../forms/d/e/<formId>/viewform` 의 가운데 부분입니다.
4. 폼 응답을 스프레드시트에 연결하면, 학생이 “제출”할 때마다 자동으로 한 줄씩 쌓입니다.

인쇄(PDF 저장)와 JSON 다운로드는 어떤 모드에서든 항상 가능합니다.

## 교사 대시보드 (`teacher.html`)

학생 제출을 **반별로 누적·집계**해서 보는 교사용 화면입니다. 서버 없이 동작하며,
같은 사이트의 `…github.io/<저장소>/teacher.html` 로 함께 배포됩니다. (학생용 `index.html` 과 분리)

데이터를 넣는 방법 두 가지:

1. **파일 가져오기** (설정 불필요): 학생이 `download` 모드로 제출한 보고서 JSON들을 끌어다 놓으면
   누적 집계됩니다. 데이터는 **이 브라우저(localStorage)에만** 저장되어(외부 전송 없음) 다시 열어도 유지됩니다.
2. **구글 시트 CSV**: `googleForm` 제출을 쓰는 경우, 응답 시트를
   **파일 → 공유 → 웹에 게시 → 쉼표로 구분된 값(.csv)** 으로 게시한 URL을 넣으면 불러옵니다.
   응답에 `payload` 열(전체 JSON)이 있으면 문항별 분석까지, 없으면 이름·점수·서술형만 집계됩니다.
   ⚠️ 게시 링크는 공개되므로 학생 개인정보 취급에 유의하세요.

집계 화면:

- **개요**: 제출 인원, 유도확인·형성평가 반 평균, 서술형 작성률, **가장 정답률 낮은 문항 top 3**(피드백 지점)
- **학생 명단**: 정렬 가능한 표. 행을 클릭하면 그 학생의 예측·정오답·서술형 전문을 펼쳐 봄
- **문항 분석**: 문항별 정답률과 선택지 분포(어떤 오답을 골랐는지), 예측(사전 개념) 분포
- **서술형**: 학생별 서술형 답안 열람
- **CSV 내보내기 / 모두 지우기**

## AI 서술형 피드백 (Step 07)

- 학생이 **강사에게 받은 Claude API 키(`sk-ant-...`)** 를 입력하면, 그 키는
  **해당 브라우저의 `localStorage` 에만** 저장되고 우리 서버로는 전송되지 않습니다.
  브라우저에서 Anthropic API(`api.anthropic.com`)를 직접 호출합니다.
- 사용 모델은 `index.html` 상단 상수 `AI_MODEL` 로 바꿀 수 있습니다.
  - `claude-haiku-4-5` (가장 저렴) · `claude-sonnet-5` (기본, 균형) · `claude-opus-5` (최고 품질)
- 브라우저 직접 호출을 위해 요청에 `anthropic-dangerous-direct-browser-access: true` 헤더를 사용합니다.
  **API 키는 학생이 볼 수 있으므로**, 사용량이 제한된 전용 키를 발급해 배포하는 것을 권장합니다.
  (AI 피드백을 쓰지 않아도 나머지 7단계는 정상 동작합니다.)

## 파일 구성

```
index.html                        단일 파일 정적 웹앱 (UI + 로직 + 시뮬레이터 + AI 호출)
.github/workflows/deploy-pages.yml GitHub Pages 자동 배포 워크플로
.nojekyll                         Pages 의 Jekyll 처리 비활성화
README.md
```

## 커스터마이즈

- 문항: `index.html` 의 `PREDICT`, `CHECK`, `QUIZ`, `ESSAY`, `DERIV` 배열 수정
- 디자인 토큰: `<style>` 의 `:root` CSS 변수 (색상은 원본의 다크/시안 테마를 따름)
- 시뮬레이터 파라미터 범위: `S_MAX`, 슬라이더 `min/max`, `computeApparent()`(억제 모델)
