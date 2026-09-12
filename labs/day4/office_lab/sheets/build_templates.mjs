import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../..');
const OUT = path.join(ROOT, 'outputs/day4-document-automation');
await fs.mkdir(OUT, { recursive: true });
const C = {ink:'#171717', navy:'#23344F', gray:'#EDF0F3', blue:'#DDE7F4', red:'#F9DAD7', redInk:'#9C2424', white:'#FFFFFF'};
const col = n => { let s=''; for(;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s; return s; };
function base(w, name, range) {
  const s=w.worksheets.add(name); s.showGridLines=false;
  s.getRange(range).format={font:{name:'Arial',size:11,color:C.ink},rowHeight:25,verticalAlignment:'center'};
  s.tabColor=C.navy; return s;
}
function header(s, range) { s.getRange(range).format={fill:C.navy,font:{bold:true,color:C.white},horizontalAlignment:'center',verticalAlignment:'center',rowHeight:30}; }
function title(s, address, text) { s.getRange(address).values=[[text]]; s.getRange(address).format.font={size:17,bold:true,color:C.ink}; s.getRange(address).format.rowHeight=32; }
function cf(s, range, formula, fill, color=C.ink) { s.getRange(range).conditionalFormats.addCustom(formula,{fill,font:{color}}); }
async function finish(w, file, previews) {
  w.recalculate();
  const scan=await w.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:15},maxChars:3000});
  console.log(file, scan.ndjson);
  for(const [sheetName,range,name] of previews) {
    const blob=await w.render({sheetName,range,scale:1.5,format:'png'});
    await fs.writeFile(path.join(OUT,name),new Uint8Array(await blob.arrayBuffer()));
  }
  await (await SpreadsheetFile.exportXlsx(w)).save(path.join(OUT,file));
}

const tasks=[
['W01','요구사항·완료 기준','PM','2026-09-14','2026-09-15',1,''],
['W02','리뷰 정책·금지 행동','AI Engineer','2026-09-16','2026-09-17',1,'W01'],
['W03','PR diff 수집','Backend','2026-09-16','2026-09-18',1,'W01'],
['W04','Codex 리뷰 초안','AI Engineer','2026-09-21','2026-09-23',0.8,'W03'],
['W05','단위 테스트·실패 사례','QA','2026-09-21','2026-09-24',0.6,'W03'],
['W06','사람 승인·게시 중복 방지','Backend','2026-09-24','2026-09-28',0.3,'W04'],
['W07','Word 문서 템플릿','PM','2026-09-18','2026-09-22',1,'W02'],
['W08','WBS·채점 Excel 템플릿','Data Analyst','2026-09-23','2026-09-25',0.7,'W07'],
['W09','PPT 보고서 생성','AI Engineer','2026-09-28','2026-09-30',0,'W08'],
['W10','문서 품질 자동 검사','QA','2026-10-01','2026-10-02',0,'W09'],
['W11','로컬 통합 화면','Frontend','2026-09-29','2026-10-02',0,'W06'],
['W12','개인정보·권한 검토','Security','2026-10-05','2026-10-06',0,'W11'],
['W13','사용자 테스트·수정','QA','2026-10-07','2026-10-08',0,'W12'],
['W14','사용 안내·릴리스','PM','2026-10-09','2026-10-09',0,'W13'],
];
await fs.writeFile(path.join(path.dirname(fileURLToPath(import.meta.url)),'wbs_tasks.json'),JSON.stringify(tasks.map(([id,task,role,start,end,progress,predecessor])=>({id,task,role,start,end,progress,predecessor})),null,2)+'\n');
const wbs=Workbook.create(), s=base(wbs,'WBS','A1:AM28');
title(s,'A2','PR 리뷰·문서 자동화 출시 WBS');
s.getRange('A4:C5').values=[['기준일',new Date('2026-09-25T00:00:00Z'),'수업용 고정 날짜'],['시작일',new Date('2026-09-14T00:00:00Z'),'4주 계획 · 토·일 제외, 공휴일 미반영']];
s.getRange('B4:B5').setNumberFormat('yyyy-mm-dd'); s.getRange('B4:B5').format.fill=C.blue;
s.getRange('F4:I5').values=[['전체 업무','완료','지연','평균 진척률'],[null,null,null,null]];
s.getRange('F5:I5').formulas=[['=COUNTA(A9:A22)','=COUNTIFS(I9:I22,"완료")','=COUNTIFS(I9:I22,"지연")','=AVERAGE(F9:F22)']];
s.getRange('I5').setNumberFormat('0%');
s.getRange('A7').values=[['입력: B4:B5, A:G | 계산: H:K | 간트: 진척 중=네이비, 완료=회색, 지연=연한 빨강']];
s.getRange('A8:K8').values=[['ID','업무','Role','시작일','종료일','진척률','선행 ID','업무일','상태','입력 확인','선행 종료']]; header(s,'A8:AM8');
s.getRange('A9:G22').values=tasks.map(([id,t,r,a,b,p,pre])=>[id,t,r,new Date(a+'T00:00:00Z'),new Date(b+'T00:00:00Z'),p,pre]);
s.getRange('D9:E22').setNumberFormat('mm/dd'); s.getRange('F9:F22').setNumberFormat('0%');s.getRange('K9:K22').setNumberFormat('mm/dd');
s.getRange('A9:G22').format.fill='#F4F7FB';
for(let r=9;r<=22;r++) {
 s.getRange(`K${r}`).formulas=[[`=IF(G${r}="","",IF(COUNTIFS($A$9:$A$22,G${r})<>1,"선행 ID 확인",VLOOKUP(G${r},$A$9:$E$22,5,FALSE)))`]];
 s.getRange(`J${r}`).formulas=[[`=IF(OR(A${r}="",B${r}="",C${r}=""),"필수 입력 누락",IF(COUNTIFS($A$9:$A$22,A${r})<>1,"중복 ID",IF(OR(NOT(ISNUMBER(D${r})),NOT(ISNUMBER(E${r}))),"날짜 확인",IF(E${r}<D${r},"종료일 확인",IF(OR(NOT(ISNUMBER(F${r})),F${r}<0,F${r}>1),"진척률 확인",IF(G${r}="","입력 완료",IF(OR(G${r}=A${r},COUNTIFS($A$9:$A$22,G${r})<>1),"선행 ID 확인",IF(D${r}<=K${r},"선행 일정 충돌","입력 완료"))))))))`]];
 s.getRange(`H${r}`).formulas=[[`=IF(J${r}<>"입력 완료","계산 보류",NETWORKDAYS(D${r},E${r}))`]];
 s.getRange(`I${r}`).formulas=[[`=IF(J${r}<>"입력 완료","입력 확인",IF(F${r}=1,"완료",IF(E${r}<$B$4,"지연",IF(D${r}>$B$4,"예정","진행 중"))))`]];
}
s.getRange('F9:F22').dataValidation={rule:{type:'decimal',operator:'between',formula1:0,formula2:1}};
for(let i=0;i<28;i++) { const c=col(12+i); s.getRange(`${c}8`).formulas=[[`=$B$5+${i}`]]; }
s.getRange('L8:AM8').setNumberFormat('mm/dd'); s.getRange('L9:AM22').values=Array.from({length:14},()=>Array(28).fill(''));
cf(s,'L9:AM22','AND($J9="입력 완료",L$8>=$D9,L$8<=$E9,WEEKDAY(L$8,2)<6,$F9=1)','#AAB5C3');
cf(s,'L9:AM22','AND($J9="입력 완료",L$8>=$D9,L$8<=$E9,WEEKDAY(L$8,2)<6,$F9<1,$E9<$B$4)',C.red);
cf(s,'L9:AM22','AND($J9="입력 완료",L$8>=$D9,L$8<=$E9,WEEKDAY(L$8,2)<6,$F9<1,$E9>=$B$4)',C.navy);
cf(s,'I9:J22','$J9<>"입력 완료"',C.red,C.redInk); cf(s,'I9:I22','$I9="지연"',C.red,C.redInk);
for(const [c,width] of [['A',8],['B',29],['C',17],['D:E',11],['F',10],['G:H',10],['I',11],['J',19],['K',12],['L:AM',6]])s.getRange(c.includes(':')?c.split(':').map(x=>x+'1').join(':'):c+'1').format.columnWidth=width;
s.freezePanes.freezeRows(8);s.freezePanes.freezeColumns(3);
s.getRange('A25').values=[['실습: W04 진척률을 100%로 변경 → 지연 1건 감소. B4를 10/01로 변경 → 상태·간트 재계산.']];
s.getRange('A27').values=[['데이터: 강의용 합성 프로젝트. 대한민국 공휴일을 반영하려면 휴일 범위와 NETWORKDAYS의 세 번째 인수를 추가하세요.']];
const before=s.getRange('I12').values[0][0]; s.getRange('F12').values=[[1]];const after=s.getRange('I12').values[0][0]; s.getRange('F12').values=[[0.8]];
if(before!=='지연'||after!=='완료')throw Error('WBS input-change failed '+JSON.stringify({before,after}));
await finish(wbs,'WBS_Gantt.xlsx',[['WBS','A1:K23','wbs_table.png'],['WBS','L7:AM23','wbs_gantt.png']]);

const exam=Workbook.create(), e=base(exam,'채점','A1:AX51'), d=base(exam,'채점내역','A1:AQ36');
const key=Array.from({length:40},(_,i)=>i%4+1);
const students=Array.from({length:28},(_,i)=>({id:`S${String(i+1).padStart(3,'0')}`,attendance:i===27?'결시':'응시',answers:Array.from({length:40},(_,q)=>(i*11+q*7)%10<(5+i%4)?key[q]:(key[q]%4+1))}));
students[24].answers[3]=null; students[24].answers[10]=null; students[25].answers[8]=9; students[26].answers=students[0].answers.slice(); students[27].answers=Array(40).fill(null);
await fs.writeFile(path.join(path.dirname(fileURLToPath(import.meta.url)),'exam_sample.json'),JSON.stringify({source:'강의용 합성 데이터. 실제 수강생 성적 아님.',key,students},null,2)+'\n');
title(e,'A2','중간고사 자동 채점');
e.getRange('A3').values=[['합성 데이터 28명 · 40문항 · 문항별 1점 · 원본 성적 및 개인정보 미포함']];
e.getRange('A4:C5').values=[['응시 인원','채점 가능','평균 점수'],[null,null,null]];
e.getRange('A5').formulas=[['=COUNTIFS(C10:C37,"응시")']]; e.getRange('B5').formulas=[['=COUNT(AR10:AR37)']];e.getRange('C5').formulas=[['=IF(COUNT(AR10:AR37)=0,"채점 보류",AVERAGE(AR10:AR37))']];e.getRange('C5').setNumberFormat('0.0');
e.getRange('E4').values=[['입력 오류']]; e.getRange('H4').values=[['결시']];e.getRange('E5').formulas=[['=COUNTIFS(AT10:AT37,"입력 오류")']];e.getRange('H5').formulas=[['=COUNTIFS(C10:C37,"결시")']];
e.getRange('A6').values=[['정답 등록']];e.getRange('B6').formulas=[['=COUNTIFS(D45:AQ45,"등록")']];
e.getRange('D6').values=[['정답=연한 네이비 · 오답=회색 · 미응답/잘못된 입력=연한 빨강. 오류는 0점이 아닌 채점 보류.']];
e.getRange('A8:C8').values=[['정답',null,null]];e.getRange('D8:AQ8').values=[key];e.getRange('D8:AQ8').format.fill=C.blue;
e.getRange('A9:AX9').values=[['학습자 ID','비고','응시 상태',...Array.from({length:40},(_,i)=>String(i+1)),'총점 /40','등수','처리 상태','미응답','입력 오류','오답','정답']];header(e,'A9:AX9');
e.getRange('A10:AQ37').values=students.map((x,i)=>[x.id,i===24?'미응답 예시':i===25?'잘못된 입력 예시':i===26?'동점 예시':'',x.attendance,...x.answers]);
title(d,'A2','문항별 채점 내역');d.getRange('A3').values=[['입력 원본은 채점 시트. 이 시트는 문항별 판정 수식이며 총점·오류 집계의 근거입니다.']];
d.getRange('A7:AQ7').values=[['학습자 ID','응시 상태','',...Array.from({length:40},(_,i)=>String(i+1))]];header(d,'A7:AQ7');
for(let i=0;i<28;i++){
 const r=i+10,dr=i+8;
 d.getRange(`A${dr}:B${dr}`).formulas=[[`='채점'!A${r}`,`='채점'!C${r}`]];
 const formulas=key.map((_,q)=>{const c=col(q+4);return `=IF('채점'!$C${r}="결시","결시",IF('채점'!${c}$45<>"등록","정답 미등록",IF('채점'!${c}${r}="","미응답",IF(NOT(ISNUMBER('채점'!${c}${r})),"잘못된 입력",IF(OR('채점'!${c}${r}<1,'채점'!${c}${r}>4,MOD('채점'!${c}${r},1)<>0),"잘못된 입력",IF('채점'!${c}${r}='채점'!${c}$8,"정답","오답"))))))`;});
 d.getRange(`D${dr}:AQ${dr}`).formulas=[formulas];
 for(const [dest,status]of [['AU','미응답'],['AV','잘못된 입력'],['AW','오답'],['AX','정답']])e.getRange(`${dest}${r}`).formulas=[[`=COUNTIFS('채점내역'!D${dr}:AQ${dr},"${status}")`]];
 e.getRange(`AT${r}`).formulas=[[`=IF(OR(A${r}="",COUNTIFS($A$10:$A$37,A${r})<>1),"ID 확인",IF(C${r}="결시","결시",IF(C${r}<>"응시","응시 상태 확인",IF(COUNTIFS('채점내역'!D${dr}:AQ${dr},"정답 미등록")>0,"정답 확인",IF(AV${r}>0,"입력 오류",IF(AU${r}>0,"미응답 포함","채점 완료"))))))`]];
 e.getRange(`AR${r}`).formulas=[[`=IF(OR(AT${r}="채점 완료",AT${r}="미응답 포함"),AX${r},"채점 보류")`]];
 e.getRange(`AS${r}`).formulas=[[`=IF(ISNUMBER(AR${r}),1+COUNTIFS($AR$10:$AR$37,">"&AR${r}),"순위 제외")`]];
}
e.getRange('A40:C45').values=[['문항 분석',null,null],['정답자 수',null,null],['집계 대상',null,null],['정답률',null,null],['미응답 수',null,null],['정답 확인',null,null]];
for(let q=0;q<40;q++){const c=col(q+4);
e.getRange(`${c}40`).values=[[q+1]];
e.getRange(`${c}41`).formulas=[[`=COUNTIFS('채점내역'!${c}8:${c}35,"정답",$AT$10:$AT$37,"채점 완료")+COUNTIFS('채점내역'!${c}8:${c}35,"정답",$AT$10:$AT$37,"미응답 포함")`]];
e.getRange(`${c}42`).formulas=[['=COUNT($AR$10:$AR$37)']];
e.getRange(`${c}43`).formulas=[[`=IF(OR(${c}42=0,${c}45<>"등록"),"집계 보류",${c}41/${c}42)`]];
e.getRange(`${c}44`).formulas=[[`=COUNTIFS('채점내역'!${c}8:${c}35,"미응답",$AT$10:$AT$37,"미응답 포함")`]];
e.getRange(`${c}45`).formulas=[[`=IF(NOT(ISNUMBER(${c}8)),"확인",IF(AND(${c}8>=1,${c}8<=4,MOD(${c}8,1)=0),"등록","확인"))`]];
}
header(e,'A40:AQ40');e.getRange('D43:AQ43').setNumberFormat('0%');
e.getRange('A48').formulas=[['="정답률 분모: 입력 오류가 없는 응시자 "&B5&"명. 결시·입력 오류 행 제외, 미응답은 분모에 포함하며 0점 처리."']];
e.getRange('A49').values=[['동점 등수: 같은 점수는 같은 등수, 다음 등수는 인원수만큼 건너뜀. 결시·오류·정답 미등록은 총점과 등수 미확정.']];
e.getRange('A50').values=[['실습: 정답 D8 변경 → 총점·동점 순위·정답률 재계산. L35의 9를 1~4로 수정 → 집계 대상 증가.']];
e.getRange('C10:C37').dataValidation={rule:{type:'list',values:['응시','결시']}};
e.getRange('D8:AQ8').dataValidation={rule:{type:'whole',operator:'between',formula1:1,formula2:4}};
e.getRange('D10:AQ37').dataValidation={rule:{type:'whole',operator:'between',formula1:1,formula2:4}};
cf(e,'D10:AQ37','AND($C10="응시",D$45="등록",ISNUMBER(D10),D10=D$8,D10>=1,D10<=4)',C.blue);
cf(e,'D10:AQ37','IF(ISNUMBER(D10),AND($C10="응시",ISNUMBER(D$8),D10<>D$8,D10>=1,D10<=4,D$8>=1,D$8<=4,MOD(D10,1)=0),FALSE)','#F1F2F4');
cf(e,'D10:AQ37','AND($C10="응시",IF(ISNUMBER(D10),OR(D10<1,D10>4,MOD(D10,1)<>0),TRUE))',C.red,C.redInk);
cf(e,'AT10:AT37','AND($AT10<>"채점 완료",$AT10<>"결시")',C.red,C.redInk);
cf(e,'D8:AQ8','IF(ISNUMBER(D8),OR(D8<1,D8>4,MOD(D8,1)<>0),TRUE)',C.red,C.redInk);
cf(e,'D43:AQ43','AND(ISNUMBER(D43),D43<0.5)',C.red,C.redInk);
cf(d,'D8:AQ35','D8="정답"',C.blue); cf(d,'D8:AQ35','OR(D8="미응답",D8="잘못된 입력",D8="정답 미등록")',C.red,C.redInk);
for(const x of [e,d]){x.getRange('A1').format.columnWidth=13;x.getRange('B1').format.columnWidth=23;x.getRange('C1').format.columnWidth=13;x.getRange('D1:AQ1').format.columnWidth=x===e?5.5:15;x.freezePanes.freezeRows(x===e?9:7);x.freezePanes.freezeColumns(3);}
e.getRange('AR1:AS1').format.columnWidth=12;e.getRange('AT1').format.columnWidth=19;e.getRange('AU1:AX1').format.columnWidth=12;
const orig=e.getRange('AR10').values[0][0];e.getRange('D8').values=[[2]];const changed=e.getRange('AR10').values[0][0];e.getRange('D8').values=[[1]];
if(orig===changed)throw Error('Exam key-change did not recalculate');
const valid=e.getRange('B5').values[0][0];e.getRange('L35').values=[[1]];const repaired=e.getRange('B5').values[0][0];e.getRange('L35').values=[[9]];
if(valid!==26||repaired!==27)throw Error('Exam row gate failed '+JSON.stringify({valid,repaired}));
e.getRange('D8').values=[[null]];const missing=e.getRange('AR10').values[0][0];e.getRange('D8').values=[[1]];if(missing!=='채점 보류')throw Error('Missing key not blocked');
e.getRange('D10').values=[['wrong']];const invalidText=e.getRange('AT10').values[0][0];e.getRange('D10').values=[[1]];if(invalidText!=='입력 오류')throw Error('Text answer not blocked');
e.getRange('D8').values=[['wrong']];const invalidTextKey=e.getRange('AT10').values[0][0];e.getRange('D8').values=[[1]];if(invalidTextKey!=='정답 확인')throw Error('Text key not blocked');
await finish(exam,'Exam_Grading.xlsx',[['채점','A1:Q20','exam_inputs.png'],['채점','AR8:AX38','exam_results.png'],['채점','A40:P50','exam_question_analysis.png'],['채점내역','A1:K18','exam_detail.png']]);
await fs.writeFile(path.join(OUT,'excel_validation.json'),JSON.stringify({wbs:{before,after},exam:{scoreBefore:orig,scoreAfter:changed,eligibleBefore:valid,eligibleAfterRepair:repaired,missingKeyResult:missing},engine:'artifact-tool 2.x',nativeEngine:'pending LibreOffice verification'},null,2)+'\n');
