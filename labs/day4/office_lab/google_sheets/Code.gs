/**
 * @OnlyCurrentDoc
 * 합성 데이터 전용 선택 실습. 기존 시트를 수정하거나 외부 문서에 접근하지 않습니다.
 * 실제 Google Sheets 실행은 수강생 계정에서 별도 검증해야 합니다.
 */
const DAY4_SHEET = 'Day4_채점_실습';
const DAY4_DETAIL = 'Day4_채점내역_실습';

function day4Column_(number) {
  let value = '';
  for (; number; number = Math.floor((number - 1) / 26)) {
    value = String.fromCharCode(65 + (number - 1) % 26) + value;
  }
  return value;
}

function day4Sample_() {
  const key = Array.from({length: 40}, (_, q) => q % 4 + 1);
  const students = Array.from({length: 28}, (_, i) => ({
    id: 'S' + String(i + 1).padStart(3, '0'),
    attendance: i === 27 ? '결시' : '응시',
    answers: Array.from({length: 40}, (_, q) => (i * 11 + q * 7) % 10 < 5 + i % 4 ? key[q] : key[q] % 4 + 1)
  }));
  students[24].answers[3] = '';
  students[24].answers[10] = '';
  students[25].answers[8] = 9;
  students[26].answers = students[0].answers.slice();
  students[27].answers = Array(40).fill('');
  return {key: key, students: students};
}

/** Pure plan: testable in Node without Google credentials. */
function day4Plan_() {
  const sample = day4Sample_();
  const main = [], detail = [];
  function put(list, range, values, formula) {
    list.push({range: range, values: values, formula: Boolean(formula)});
  }
  put(main, 'A2', [['중간고사 자동 채점']]);
  put(main, 'A3', [['합성 28명·40문항. 원본 시험 파일 또는 실제 성적을 사용하지 않습니다.']]);
  put(main, 'A4:C4', [['응시 인원', '채점 가능', '평균 점수']]);
  put(main, 'A5:C5', [['=COUNTIFS(C10:C37,"응시")', '=COUNT(AR10:AR37)', '=IF(COUNT(AR10:AR37)=0,"채점 보류",AVERAGE(AR10:AR37))']], true);
  put(main, 'A6:B6', [['정답 등록', null]]);
  put(main, 'B6', [['=COUNTIFS(D45:AQ45,"등록")']], true);
  put(main, 'D6', [['정답=네이비 계열, 오답=회색, 미응답·잘못된 입력=연한 빨강']]);
  put(main, 'A8', [['정답']]);
  put(main, 'D8:AQ8', [sample.key]);
  put(main, 'A9:AX9', [['학습자 ID', '비고', '응시 상태', ...sample.key.map((_, i) => String(i + 1)), '총점 /40', '등수', '처리 상태', '미응답', '입력 오류', '오답', '정답']]);
  put(main, 'A10:AQ37', sample.students.map((s, i) => [s.id, i === 24 ? '미응답 예시' : i === 25 ? '잘못된 입력 예시' : i === 26 ? '동점 예시' : '', s.attendance, ...s.answers]));
  put(detail, 'A2', [['문항별 채점 내역']]);
  put(detail, 'A3', [['입력은 Day4_채점_실습 시트. 총점·오류 집계의 근거를 문항별로 표시합니다.']]);
  put(detail, 'A7:AQ7', [['학습자 ID', '응시 상태', '', ...sample.key.map((_, i) => String(i + 1))]]);
  for (let i = 0; i < 28; i++) {
    const row = i + 10, drow = i + 8;
    put(detail, 'A' + drow + ':B' + drow, [["='" + DAY4_SHEET + "'!A" + row, "='" + DAY4_SHEET + "'!C" + row]], true);
    const answers = sample.key.map((_, q) => {
      const c = day4Column_(q + 4), input = "'" + DAY4_SHEET + "'!" + c + row, key = "'" + DAY4_SHEET + "'!" + c + '$8';
      return '=IF(\'' + DAY4_SHEET + '\'!$C' + row + '="결시","결시",IF(\'' + DAY4_SHEET + '\'!' + c + '$45<>"등록","정답 미등록",IF(' + input + '="","미응답",IF(NOT(ISNUMBER(' + input + ')),"잘못된 입력",IF(OR(' + input + '<1,' + input + '>4,MOD(' + input + ',1)<>0),"잘못된 입력",IF(' + input + '=' + key + ',"정답","오답"))))))';
    });
    put(detail, 'D' + drow + ':AQ' + drow, [answers], true);
    const counts = ['미응답', '잘못된 입력', '오답', '정답'].map(s => '=COUNTIFS(\'' + DAY4_DETAIL + '\'!D' + drow + ':AQ' + drow + ',"' + s + '")');
    put(main, 'AU' + row + ':AX' + row, [counts], true);
    const status = '=IF(OR(A' + row + '="",COUNTIFS($A$10:$A$37,A' + row + ')<>1),"ID 확인",IF(C' + row + '="결시","결시",IF(C' + row + '<>"응시","응시 상태 확인",IF($B$6<>40,"정답 확인",IF(AV' + row + '>0,"입력 오류",IF(AU' + row + '>0,"미응답 포함","채점 완료"))))))';
    put(main, 'AT' + row, [[status]], true);
    put(main, 'AR' + row, [['=IF(OR(AT' + row + '="채점 완료",AT' + row + '="미응답 포함"),AX' + row + ',"채점 보류")']], true);
    put(main, 'AS' + row, [['=IF(ISNUMBER(AR' + row + '),1+COUNTIFS($AR$10:$AR$37,">"&AR' + row + '),"순위 제외")']], true);
  }
  put(main, 'A40:A45', [['문항 분석'], ['정답자 수'], ['집계 대상'], ['정답률'], ['미응답 수'], ['정답 확인']]);
  put(main, 'D40:AQ40', [sample.key.map((_, i) => i + 1)]);
  for (let q = 0; q < 40; q++) {
    const c = day4Column_(q + 4), dr = "'" + DAY4_DETAIL + "'!" + c + '8:' + c + '35';
    put(main, c + '41', [['=COUNTIFS(' + dr + ',"정답",$AT$10:$AT$37,"채점 완료")+COUNTIFS(' + dr + ',"정답",$AT$10:$AT$37,"미응답 포함")']], true);
    put(main, c + '42', [['=COUNT($AR$10:$AR$37)']], true);
    put(main, c + '43', [['=IF(OR(' + c + '42=0,' + c + '45<>"등록"),"집계 보류",' + c + '41/' + c + '42)']], true);
    put(main, c + '44', [['=COUNTIFS(' + dr + ',"미응답",$AT$10:$AT$37,"미응답 포함")']], true);
    put(main, c + '45', [['=IF(NOT(ISNUMBER(' + c + '8)),"확인",IF(AND(' + c + '8>=1,' + c + '8<=4,MOD(' + c + '8,1)=0),"등록","확인"))']], true);
  }
  put(main, 'A48', [['="정답률 분모: 오류 없는 응시자 "&B5&"명. 결시·입력 오류 제외, 미응답 포함(0점)."']], true);
  put(main, 'A49', [['동점은 같은 등수. 다음 순위는 동점 인원만큼 건너뜁니다. 오류·결시는 점수 미확정입니다.']]);
  put(main, 'A50', [['실습: L35의 9를 1로 복구 → 27명 집계. D8의 정답을 변경 → 총점·순위·정답률 재계산.']]);
  return {sample: sample, main: main, detail: detail};
}

function day4Format_(sheet, detail) {
  sheet.getRange('A1:AX50').setFontFamily('Arial').setFontSize(11).setFontColor('#171717').setVerticalAlignment('middle');
  sheet.setHiddenGridlines(true);
  sheet.setRowHeights(1, 50, 26);
  sheet.setColumnWidth(1, 115);
  sheet.setColumnWidth(2, 175);
  sheet.setColumnWidth(3, 105);
  sheet.setColumnWidths(4, 40, detail ? 110 : 45);
  sheet.setColumnWidths(44, 7, 100);
  sheet.setColumnWidth(46, 145);
  sheet.getRange('A2').setFontSize(17).setFontWeight('bold');
  sheet.getRange(detail ? 'A7:AQ7' : 'A9:AX9').setBackground('#23344F').setFontColor('#FFFFFF').setFontWeight('bold').setHorizontalAlignment('center');
  sheet.setFrozenRows(detail ? 7 : 9);
  sheet.setFrozenColumns(3);
  if (!detail) {
    sheet.getRange('A40:AQ40').setBackground('#23344F').setFontColor('#FFFFFF').setFontWeight('bold');
    sheet.getRange('D8:AQ8').setBackground('#DDE7F4');
    sheet.getRange('D43:AQ43').setNumberFormat('0%');
    sheet.getRange('C5').setNumberFormat('0.0');
  }
}

function day4Rules_(sheet, detail) {
  function rule(range, formula, fill) {
    return SpreadsheetApp.newConditionalFormatRule().whenFormulaSatisfied(formula).setBackground(fill).setRanges([sheet.getRange(range)]).build();
  }
  // Google Sheets custom rules reference only cells on their own sheet.
  const rules = detail ? [
    rule('D8:AQ35', '=D8="정답"', '#DDE7F4'),
    rule('D8:AQ35', '=OR(D8="미응답",D8="잘못된 입력",D8="정답 미등록")', '#F9DAD7')
  ] : [
    rule('D10:AQ37', '=AND($C10="응시",D$45="등록",ISNUMBER(D10),D10=D$8,D10>=1,D10<=4)', '#DDE7F4'),
    rule('D10:AQ37', '=IF(ISNUMBER(D10),AND($C10="응시",ISNUMBER(D$8),D10<>D$8,D10>=1,D10<=4,D$8>=1,D$8<=4,MOD(D10,1)=0),FALSE)', '#F1F2F4'),
    rule('D10:AQ37', '=AND($C10="응시",IF(ISNUMBER(D10),OR(D10<1,D10>4,MOD(D10,1)<>0),TRUE))', '#F9DAD7'),
    rule('D8:AQ8', '=IF(ISNUMBER(D8),OR(D8<1,D8>4,MOD(D8,1)<>0),TRUE)', '#F9DAD7'),
    rule('AT10:AT37', '=AND($AT10<>"채점 완료",$AT10<>"결시")', '#F9DAD7')
  ];
  sheet.setConditionalFormatRules(rules);
}

/** Run manually from a container-bound Apps Script project. */
function createDay4GradingPractice() {
  const ui = SpreadsheetApp.getUi();
  const answer = ui.alert('4주차 합성 채점 실습',
    '현재 문서에 Day4_채점_실습과 Day4_채점내역_실습을 새로 만듭니다. 기존 시트는 수정하지 않습니다. 빈 연습 문서가 맞습니까?', ui.ButtonSet.YES_NO);
  if (answer !== ui.Button.YES) return {status: 'CANCELLED'};
  // Acquire the lock after the dialog: Google UI dialogs release pre-existing locks.
  const lock = LockService.getDocumentLock();
  if (!lock || !lock.tryLock(5000)) throw new Error('DOCUMENT_BUSY');
  try {
    const document = SpreadsheetApp.getActiveSpreadsheet();
    if (!document) throw new Error('BOUND_SPREADSHEET_REQUIRED');
    if (document.getSheetByName(DAY4_SHEET) || document.getSheetByName(DAY4_DETAIL)) {
      throw new Error('PRACTICE_SHEET_ALREADY_EXISTS: 새 빈 연습 문서에서 실행하세요.');
    }
    const plan = day4Plan_();
    const main = document.insertSheet(DAY4_SHEET);
    const detail = document.insertSheet(DAY4_DETAIL);
    [main, detail].forEach(sheet => {
      const count = sheet.getMaxColumns();
      if (count < 50) sheet.insertColumnsAfter(count, 50 - count);
    });
    [[main, plan.main, false], [detail, plan.detail, true]].forEach(item => {
      item[1].forEach(write => {
        const range = item[0].getRange(write.range);
        if (write.formula) range.setFormulas(write.values);
        else range.setValues(write.values.map(row => row.map(value => value === null ? '' : value)));
      });
      day4Format_(item[0], item[2]);
      day4Rules_(item[0], item[2]);
    });
    const answers = SpreadsheetApp.newDataValidation().requireNumberBetween(1, 4).setAllowInvalid(true).setHelpText('정수1~4. 잘못된 입력은 처리 상태에서 채점 보류로 표시됩니다.').build();
    main.getRange('D8:AQ8').setDataValidation(answers);
    main.getRange('D10:AQ37').setDataValidation(answers);
    main.getRange('C10:C37').setDataValidation(SpreadsheetApp.newDataValidation().requireValueInList(['응시', '결시'], true).setAllowInvalid(false).build());
    SpreadsheetApp.flush();
    ui.alert('생성 완료', '새 합성 시트에서 정답과 L35의 오류 입력을 바꾸어 총점·순위·정답률을 확인하세요. 실제 성적을 붙여넣지 마세요.', ui.ButtonSet.OK);
    return {status: 'CREATED', sheets: [DAY4_SHEET, DAY4_DETAIL]};
  } finally {
    lock.releaseLock();
  }
}
