import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import test from 'node:test';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const code = fs.readFileSync(path.join(HERE, 'Code.gs'), 'utf8');
function number(c) { return [...c].reduce((n, x) => n * 26 + x.charCodeAt(0) - 64, 0); }
function dimensions(range) {
  const match = /^([A-Z]+)(\d+)(?::([A-Z]+)(\d+))?$/.exec(range);
  assert.ok(match, range);
  return [Number(match[4] || match[2]) - Number(match[2]) + 1, number(match[3] || match[1]) - number(match[1]) + 1];
}
function harness({answer = 'YES', existing = [], busy = false, failWrite = false} = {}) {
  const state = {created: [], writes: [], rules: [], released: 0, lockAttempts: 0};
  function range(sheet, address) {
    const value = {};
    ['setValues', 'setFormulas'].forEach(method => {
      value[method] = matrix => {
        if (failWrite) throw new Error('TEST_WRITE_FAILURE');
        const [rows, columns] = dimensions(address);
        assert.equal(matrix.length, rows, address);
        matrix.forEach(row => assert.equal(row.length, columns, address));
        state.writes.push({sheet, address, method, matrix}); return value;
      };
    });
    ['setFontFamily', 'setFontSize', 'setFontColor', 'setVerticalAlignment', 'setFontWeight', 'setBackground', 'setHorizontalAlignment', 'setNumberFormat', 'setDataValidation'].forEach(method => value[method] = () => value);
    return value;
  }
  function sheet(name) {
    const value = {getRange: address => range(name, address), getMaxColumns: () => 26,
      setConditionalFormatRules: rules => state.rules.push(...rules)};
    ['insertColumnsAfter', 'setHiddenGridlines', 'setRowHeights', 'setColumnWidth', 'setColumnWidths', 'setFrozenRows', 'setFrozenColumns'].forEach(method => value[method] = () => value);
    return value;
  }
  function builder() {
    const value = {data: {}};
    ['whenFormulaSatisfied', 'setBackground', 'setRanges', 'requireNumberBetween', 'setAllowInvalid', 'setHelpText', 'requireValueInList'].forEach(method => value[method] = (...args) => { value.data[method] = args; return value; });
    value.build = () => value.data;
    return value;
  }
  const context = vm.createContext({SpreadsheetApp: {
    getUi: () => ({Button: {YES: 'YES'}, ButtonSet: {YES_NO: 'YES_NO', OK: 'OK'}, alert: () => answer}),
    getActiveSpreadsheet: () => ({getSheetByName: name => existing.includes(name) ? {mustNotTouch: true} : null,
      insertSheet: name => { state.created.push(name); return sheet(name); }}),
    newConditionalFormatRule: builder, newDataValidation: builder, flush() {},
  }, LockService: {getDocumentLock: () => ({tryLock: () => {state.lockAttempts++; return !busy;}, releaseLock: () => state.released++})}});
  vm.runInContext(code, context);
  return {state, context, run: () => context.createDay4GradingPractice()};
}

test('synthetic data matches local Python fixture exactly', () => {
  const {context} = harness();
  const actual = JSON.parse(JSON.stringify(context.day4Sample_()));
  const expected = JSON.parse(fs.readFileSync(path.join(HERE, '../sheets/exam_sample.json'), 'utf8'));
  expected.students.forEach(row => row.answers = row.answers.map(value => value === null ? '' : value));
  assert.deepEqual(actual, {key: expected.key, students: expected.students});
});
test('creates only two new sheets and writes correct rectangular shapes', () => {
  const h = harness({existing: ['나의 기존 자료']});
  assert.equal(h.run().status, 'CREATED');
  assert.deepEqual(h.state.created, ['Day4_채점_실습', 'Day4_채점내역_실습']);
  assert.ok(h.state.writes.length > 300);
  assert.ok(h.state.writes.every(w => h.state.created.includes(w.sheet)));
  assert.equal(h.state.released, 1);
});
test('cancel causes no document writes or lock acquisition', () => {
  const h = harness({answer: 'NO'});
  assert.equal(h.run().status, 'CANCELLED');
  assert.equal(h.state.created.length, 0);
  assert.equal(h.state.lockAttempts, 0);
});
test('duplicate sheet name aborts before any creation', () => {
  for (const existing of [['Day4_채점_실습'], ['Day4_채점내역_실습']]) {
    const h = harness({existing});
    assert.throws(h.run, /PRACTICE_SHEET_ALREADY_EXISTS/);
    assert.equal(h.state.created.length, 0);
    assert.equal(h.state.released, 1);
  }
});
test('document contention aborts without writes', () => {
  const h = harness({busy: true});
  assert.throws(h.run, /DOCUMENT_BUSY/);
  assert.equal(h.state.created.length, 0);
});
test('write failure releases lock without deleting any sheet', () => {
  const h = harness({failWrite: true});
  assert.throws(h.run, /TEST_WRITE_FAILURE/);
  assert.equal(h.state.released, 1);
});
test('conditional rules only use references on their own sheet', () => {
  const h = harness(); h.run();
  assert.equal(h.state.rules.length, 7);
  for (const rule of h.state.rules) assert.doesNotMatch(rule.whenFormulaSatisfied[0], /!|INDIRECT/i);
  assert.match(h.state.rules[0].whenFormulaSatisfied[0], /D\$45="등록"/);
});
test('formulas preserve gates, weighted-free totals, denominator and ties', () => {
  const plan = harness().context.day4Plan_();
  const get = address => plan.main.find(w => w.range === address).values[0][0];
  assert.match(get('AT10'), /ID 확인/);
  assert.match(get('AT10'), /정답 확인/);
  assert.match(get('AR10'), /채점 보류/);
  assert.equal(get('AS10'), '=IF(ISNUMBER(AR10),1+COUNTIFS($AR$10:$AR$37,">"&AR10),"순위 제외")');
  assert.equal(get('D42'), '=COUNT($AR$10:$AR$37)');
  assert.match(get('D43'), /집계 보류/);
  for (const write of [...plan.main, ...plan.detail].filter(w => w.formula)) {
    for (const row of write.values) for (const formula of row) {
      const syntax = formula.replace(/"[^"]*"/g, '').replace(/'[^']*'/g, '');
      let balance = 0;
      for (const c of syntax) { if (c === '(') balance++; if (c === ')') balance--; assert.ok(balance >= 0, formula); }
      assert.equal(balance, 0, formula);
    }
  }
});
test('scope and source contain no external access or destructive APIs', () => {
  assert.match(code, /@OnlyCurrentDoc/);
  assert.doesNotMatch(code, /openById|openByUrl|UrlFetchApp|DriveApp|GmailApp|MailApp|\.clear\(|deleteSheet|deleteRows|deleteColumns|ScriptApp/);
  const manifest = JSON.parse(fs.readFileSync(path.join(HERE, 'appsscript.json'), 'utf8'));
  assert.ok(manifest.oauthScopes.includes('https://www.googleapis.com/auth/spreadsheets.currentonly'));
  assert.equal(manifest.oauthScopes.length, 2);
});
