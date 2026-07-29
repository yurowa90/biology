/**
 * 효소반응속도 학습 워크북 — Google Apps Script 백엔드
 *
 * 배포 방법
 *  1) script.google.com 에서 새 프로젝트를 만듭니다.
 *  2) 이 파일 내용을 Code.gs 에 붙여넣습니다.
 *  3) 프로젝트에 HTML 파일을 추가하고 이름을 "Index" 로 지정한 뒤,
 *     저장소의 index.html 내용을 그대로 붙여넣습니다.
 *  4) 배포 → 새 배포 → 유형: 웹 앱
 *       - 실행: 나
 *       - 액세스 권한: 학교/조직 또는 모든 사용자
 *     배포하면 /exec 로 끝나는 URL 이 발급됩니다. 이 URL 을 학생에게 공유하세요.
 *  5) 학생이 최종 보고서를 "제출하기" 하면 아래 saveReport() 가 호출되어
 *     스프레드시트(제출_로그 시트)에 한 줄씩 기록됩니다.
 *
 * index.html 은 Apps Script 안에서 실행되면 google.script.run.saveReport() 를,
 * 정적 호스팅(GitHub Pages 등)에서는 CONFIG.submitEndpoint 로의 POST 를 자동으로 사용합니다.
 */

function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('효소반응속도 학습 워크북')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

// 정적 호스팅에서 fetch(POST) 로 제출할 때 사용되는 진입점
function doPost(e) {
  var payload = JSON.parse(e.postData.contents);
  var result = saveReport(payload);
  return ContentService
    .createTextOutput(JSON.stringify(result))
    .setMimeType(ContentService.MimeType.JSON);
}

// google.script.run.saveReport(payload) 로도, doPost 로도 호출됨
function saveReport(payload) {
  var sheet = getSheet_();
  sheet.appendRow([
    new Date(),
    payload.name || '',
    payload.studentId || '',
    payload.checkScore + '/' + payload.checkMax,
    payload.quizScore + '/' + payload.quizMax,
    JSON.stringify(payload.predict || {}),
    JSON.stringify(payload.check || {}),
    JSON.stringify(payload.quiz || {}),
    (payload.essay && payload.essay.s1) || '',
    (payload.essay && payload.essay.s2) || '',
    JSON.stringify(payload.sim || {})
  ]);
  return { ok: true };
}

function getSheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) {
    // 컨테이너에 묶이지 않은 프로젝트라면 새 스프레드시트를 만들어 재사용
    var props = PropertiesService.getScriptProperties();
    var id = props.getProperty('SHEET_ID');
    if (id) {
      ss = SpreadsheetApp.openById(id);
    } else {
      ss = SpreadsheetApp.create('효소반응속도 워크북 제출');
      props.setProperty('SHEET_ID', ss.getId());
    }
  }
  var sheet = ss.getSheetByName('제출_로그');
  if (!sheet) {
    sheet = ss.insertSheet('제출_로그');
    sheet.appendRow([
      '제출시각', '이름', '학번', '유도확인', '형성평가',
      '예측', '유도확인_답', '형성평가_답', '서술1', '서술2', '시뮬레이터'
    ]);
  }
  return sheet;
}
