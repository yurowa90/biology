# 효소반응속도 학습 워크북 · 미카엘리스–멘텐

로켓방정식(치올콥스키 식) 학습 워크북을 **생명과학 맥락**으로 옮긴 탐구형 웹앱입니다.
효소·물질대사 단원의 핵심 정량식인 **미카엘리스–멘텐 반응속도식**을 중심으로, 학생이
예측 → 유도 → 개념 → 시뮬레이션 → 평가 → 서술형 → 보고서까지 스스로 밟아 갑니다.

단일 HTML 파일(`index.html`)로 동작하며, 외부 라이브러리 없이 오프라인에서도 열립니다.

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
| 08 | 최종 보고서 (SUBMIT) | 전체 답안·점수 정리 → 구글 시트 제출 / 인쇄(PDF) / 다운로드 |

원본 로켓 워크북과의 대응:

- 치올콥스키 식 유도 ↔ 미카엘리스–멘텐 식 유도
- 연소율 ṁ, 추력 `F = vₑ·ṁ` ↔ 회전수 kcat, `Vmax = kcat·[E]₀`
- 지면/로켓 두 관점 시뮬레이터 ↔ 직접 곡선 / 이중역수 두 표현 + 억제제 효과

## 실행 방법

### A. 바로 열기 / 정적 호스팅
`index.html` 을 브라우저로 열거나 GitHub Pages 등에 올립니다. 답안과 진행 상황은
브라우저 `localStorage` 에 저장됩니다.

### B. Google Apps Script 웹앱 (원본과 동일한 배포 방식, 구글 시트 저장)
1. [script.google.com](https://script.google.com) 에서 새 프로젝트 생성
2. `apps-script/Code.gs` 내용을 `Code.gs` 에 붙여넣기
3. HTML 파일 추가 → 이름 `Index` → 저장소의 `index.html` 내용 붙여넣기
4. **배포 → 새 배포 → 웹 앱** (실행: 나 / 액세스: 조직 또는 모든 사용자)
5. 발급된 `/exec` URL 을 학생에게 공유

`index.html` 은 Apps Script 안에서 실행되면 `google.script.run.saveReport()` 를,
정적 호스팅에서는 `CONFIG.submitEndpoint` 로의 POST 를 자동으로 사용합니다.
정적 호스팅에서도 구글 시트로 제출하려면 `index.html` 상단의
`CONFIG.submitEndpoint` 에 배포된 Apps Script `/exec` URL 을 넣으세요.

## AI 서술형 피드백 (Step 07)

- 학생이 **강사에게 받은 Claude API 키(`sk-ant-...`)** 를 입력하면, 그 키는
  **해당 브라우저의 `localStorage` 에만** 저장되고 우리 서버로는 전송되지 않습니다.
  브라우저에서 Anthropic API(`api.anthropic.com`)를 직접 호출합니다.
- 사용 모델은 `index.html` 상단 상수 `AI_MODEL` 로 바꿀 수 있습니다.
  - `claude-haiku-4-5` (가장 저렴) · `claude-sonnet-5` (기본, 균형) · `claude-opus-5` (최고 품질)
- 브라우저 직접 호출을 위해 요청에 `anthropic-dangerous-direct-browser-access: true`
  헤더를 사용합니다. **API 키는 학생이 볼 수 있으므로**, 사용량이 제한된 전용 키를
  발급해 배포하는 것을 권장합니다.

## 파일 구성

```
index.html            단일 파일 웹앱 (UI + 로직 + 시뮬레이터 + AI 호출)
apps-script/Code.gs   구글 시트 저장용 Apps Script 백엔드 (선택)
README.md
```

## 커스터마이즈

- 문항: `index.html` 의 `PREDICT`, `CHECK`, `QUIZ`, `ESSAY`, `DERIV` 배열 수정
- 디자인 토큰: `<style>` 의 `:root` CSS 변수 (색상은 원본의 다크/시안 테마를 따름)
- 시뮬레이터 파라미터 범위: `S_MAX`, 슬라이더 `min/max`, `computeApparent()`(억제 모델)
