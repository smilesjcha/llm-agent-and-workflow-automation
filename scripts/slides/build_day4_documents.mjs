import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {execFileSync} from 'node:child_process';
import {Presentation, PresentationFile} from '@oai/artifact-tool';
import sharp from 'sharp';
import {OPENING, LESSONS, PERIODS, SOURCES} from './day4_document_content.mjs';
import {buildDay4Plan} from './day4_plan.mjs';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const SKILL='/Users/sungjae-cha/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations';
const PYTHON='/Users/sungjae-cha/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const BUILD=path.join(ROOT,'output/qa/day4-200/build');
const FINAL=process.env.DAY4_FINAL_PATH??path.join(ROOT,'output/qa/day4-200/final/Day4_200p_v1.pptx');
process.env.RUNTIME_NODE_MODULES??=await fs.realpath(path.join(ROOT,'node_modules'));
const {makeNativeBulletParagraphs,finalizePresentation}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
const FONT='NanumGothic',MONO='Menlo';
const C={ink:'#161616',white:'#FFFFFF',gray:'#F2F3F4',line:'#D9D9D9',muted:'#595959',navy:'#162A43'};
const deck=Presentation.create({slideSize:{width:1280,height:720}});
const tableOwners=[],manifest=[];
function shape(sl,geometry,x,y,w,h,fill='none',stroke='none'){
 return sl.shapes.add({geometry,position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width:stroke==='none'?0:1}});
}
function text(sl,value,x,y,w,h,{size=30,bold=false,color=C.ink,font=FONT,align='left'}={}){
 const box=shape(sl,'textbox',x,y,w,h);box.text=String(value);
 box.text.style={typeface:font,fontSize:size,bold,color,alignment:align,verticalAlignment:'top',wrap:'square',autoFit:'none',lineSpacing:1.12,insets:{left:0,right:0,top:0,bottom:0}};
 return box;
}
function line(sl,x,y,w,color=C.line){shape(sl,'line',x,y,w,0,'none',color);}
function footer(sl,page,dark=false){
 line(sl,64,675,1152,dark?'#555555':C.line);
 text(sl,'LLM Agent · 업무 자동화',64,686,700,24,{size:18,color:dark?'#CCCCCC':C.muted});
 text(sl,String(page).padStart(3,'0'),1116,683,100,27,{size:20,color:dark?C.white:C.ink,align:'right'});
}
function table(sl,headers,rows,{y=184,h=458,widths,headerH=62}={}){
 const w=1152,n=rows.length+1;
 const values=[headers,...rows].map(row=>row.map(String));
 const colWidths=widths??(headers.length===2?[365,787]:headers.length===3?[260,434,458]:[218,311,311,312]);
 const tb=sl.tables.add({rows:n,columns:headers.length,left:64,top:y,width:w,height:h,values,columnWidths:colWidths});
 tb.styleOptions={headerRow:true,bandedRows:false,firstColumn:false,lastColumn:false};
 tb.borders.assign({style:'solid',fill:C.line,width:1});
 // Row heights follow actual multiline content, not a uniform fixed template.
 const units=rows.map(row=>Math.max(...row.map((s,c)=>{
   const cap=Math.max(8,Math.floor(colWidths[c]/25));
   return String(s).split('\n').reduce((a,l)=>a+Math.max(1,Math.ceil([...l].reduce((k,ch)=>k+(/[\x00-\x7f]/.test(ch)?.55:1),0)/cap)),0);
 })));
 const total=units.reduce((a,b)=>a+b,0);
 for(let r=0;r<n;r++){
  tb.rows[r].height=r===0?headerH:(h-headerH)*units[r-1]/total;
  for(let c=0;c<headers.length;c++){
   const cell=tb.getCell(r,c);cell.fill=r===0?C.ink:r%2===0?C.gray:C.white;
   cell.text.style={typeface:FONT,fontSize:26,bold:r===0||c===0,color:r===0?C.white:C.ink,verticalAlignment:'middle',alignment:'left',wrap:'square',autoFit:'none',lineSpacing:1.05};
   tb.cells.block({row:r,column:c,rowCount:1,columnCount:1}).assign({margins:{left:15,right:14,top:10,bottom:10},anchor:'center'});
  }
 }
 tableOwners.push(deck.slides.items.length);
}
function bulletList(sl,items,x,y,w,h){
 const b=text(sl,'',x,y,w,h,{size:36});
 b.text=makeNativeBulletParagraphs(items,{marginLeftPoints:24,hangingPoints:12,spaceAfterPoints:30});
 b.text.style={typeface:FONT,fontSize:36,color:C.ink,autoFit:'none',wrap:'square',lineSpacing:1.18,insets:{left:0,right:0,top:0,bottom:0}};
}
async function render(d,p,page){
 const sl=deck.slides.add();sl.background.fill=C.white;
 if(d.type==='cover'){
  sl.background.fill=C.ink;
  text(sl,'LLM AGENT & WORKFLOW AUTOMATION',64,61,1152,43,{size:28,color:C.white});
  text(sl,'04',64,174,385,169,{size:144,bold:true,color:C.white});
  text(sl,d.title,64,364,1152,104,{size:66,bold:true,color:C.white});
  text(sl,d.subtitle,64,502,1152,55,{size:33,color:C.white});
  text(sl,'차성재 · Agentic AI PM / AI 겸임교수',64,598,1152,42,{size:26,color:C.white});
  footer(sl,page,true);return sl;
 }
 if(d.type==='section'){
  sl.background.fill=C.ink;const period=PERIODS[p];
  text(sl,`4주차 ${p+1}차시`,64,50,1152,50,{size:32,color:C.white,bold:true});
  text(sl,period.time,64,139,1152,89,{size:66,color:C.white,bold:true});
  text(sl,period.title,64,257,1152,86,{size:55,color:C.white,bold:true});
  text(sl,period.goal,64,376,1130,92,{size:31,color:C.white});
  text(sl,`이론 ${period.theory}분  ·  시연 ${period.demo}분  ·  작업 ${period.lab}분  ·  확인 ${period.check}분`,64,526,1140,54,{size:28,color:C.white});
  text(sl,period.files,64,601,1140,41,{size:25,color:C.white});
  footer(sl,page,true);return sl;
 }
 const phase=d.activityLabel??({theory:'이론',demo:'시연',lab:'코드·파일 작업',check:'결과 확인'}[d.phase]??'수업 안내');
 const label=d.type==='break'?d.label:`${p==null?'4주차':`4주차 ${p+1}차시 · ${PERIODS[p].time}`}  /  ${d.reference?(d.activityLabel??'선택 확장'):phase}`;
 text(sl,label,64,27,1152,34,{size:23,bold:true,color:C.muted});
 text(sl,d.title,64,82,1152,77,{size:50,bold:true});
 footer(sl,page);
 if(d.type==='table')table(sl,d.headers,d.rows,d.options??{});
 else if(d.type==='architecture'){
  const lanes=[['PR diff·제품 규칙','Codex 리뷰 + 테스트','Markdown·HTML'],['WBS·합성 답안','Python·수식 계산','Excel·PPT'],['경력 사실 목록','문장 개선 + 사실 비교','Word']];
  lanes.forEach((lane,i)=>{
   const x=64+i*394;
   [195,343,549].forEach((y,j)=>{
    shape(sl,'rect',x,y,364,87,j===1?C.gray:C.white,C.ink);
    text(sl,lane[j],x+18,y+26,328,49,{size:28,bold:j===2,align:'center'});
   });
   shape(sl,'downArrow',x+170,294,25,32,C.ink);
   shape(sl,'downArrow',x+170,508,25,29,C.ink);
  });
  shape(sl,'rect',64,458,1152,43,C.ink);
  text(sl,'대상·수치·사실·파일 확인  /  외부 전송은 별도 사람 확인',79,465,1122,32,{size:25,bold:true,color:C.white,align:'center'});
 }
 else if(d.type==='points'){
  line(sl,64,199,1152,C.ink);
  bulletList(sl,d.points,76,254,1110,366);
 }else if(d.type==='code'){
  shape(sl,'rect',64,184,1152,357,C.ink);
  text(sl,d.code,88,208,1104,315,{size:24,font:MONO,color:C.white});
  text(sl,d.explain.join('\n'),64,564,1152,88,{size:29});
 }else if(d.type==='prompt'){
  text(sl,'대화 입력 예시',64,183,1100,44,{size:28,bold:true});
  shape(sl,'rect',64,242,1152,282,C.gray);
  text(sl,d.prompt,88,266,1104,238,{size:32});
  text(sl,'확인할 내용',64,557,214,46,{size:28,bold:true});
  text(sl,d.check,285,557,931,92,{size:29});
 }else if(d.type==='task'){
  const stepPitch=d.steps.length>3?77:103;
  d.steps.forEach((step,i)=>{
   text(sl,String(i+1).padStart(2,'0'),64,191+i*stepPitch,105,68,{size:47,bold:true});
   text(sl,step,189,198+i*stepPitch,1027,74,{size:32});
  });
  line(sl,64,513,1152);
  text(sl,d.file,64,537,1152,49,{size:26,color:C.muted});
  text(sl,d.check,64,598,1152,52,{size:29,bold:true});
 }else if(d.type==='image'){
  let buf=await fs.readFile(path.join(ROOT,d.asset));
  // Crop only the slide placement; retain the untouched capture as the evidence source.
  if(d.crop)buf=await sharp(buf).extract(d.crop).png().toBuffer();
  if(d.headerAsset){
   const header=await fs.readFile(path.join(ROOT,d.headerAsset));
   sl.images.add({blob:header,contentType:'image/png',alt:'채점표 헤더 9행',fit:'contain',position:{left:64,top:178,width:1152,height:81}});
   text(sl,'10–32행 생략 · 아래는 33–37행',64,270,1152,40,{size:25,color:C.muted});
   sl.images.add({blob:buf,contentType:'image/png',alt:d.caption,fit:'contain',position:{left:64,top:320,width:1152,height:250}});
  }else sl.images.add({blob:buf,contentType:'image/png',alt:d.caption,fit:'contain',position:{left:64,top:175,width:1152,height:414}});
  text(sl,d.caption,64,610,1152,45,{size:25});
 }else if(d.type==='break'){
  text(sl,d.time,64,226,1152,95,{size:68,bold:true});
  text(sl,d.body,64,396,1152,113,{size:38});
 }else throw Error('UNKNOWN_SLIDE_TYPE '+d.type);
 return sl;
}

const {plan,ranges,total}=buildDay4Plan(OPENING,LESSONS,PERIODS);
if(plan.length!==200)throw Error('DAY4_EXPECTED_200_SLIDES');
await fs.mkdir(BUILD,{recursive:true});
for(let i=0;i<plan.length;i++){
 const {d,p,minutes}=plan[i],page=i+1;
 const sl=await render(d,p,page);
 const sources=d.sources??(p==null?[SOURCES.codex,SOURCES.claude,SOURCES.claudeFiles]:p<3?[SOURCES.github,SOURCES.reviews]:p===3?[SOURCES.networkdays,SOURCES.formatting]:p===4?[SOURCES.sheets,SOURCES.appsScript]:p===6?[SOURCES.claudeFiles,SOURCES.codex]:[SOURCES.codex,SOURCES.claude]);
 const note=[`[강사용 진행]\n권장 시간: ${minutes}분${minutes===0?' · 선택 확장 또는 쉬는 시간, 기본 학습 시간 미산정':''}`,`구간: ${p==null?'시작 안내 (1차시 50분에 포함)':`${p+1}차시 ${PERIODS[p].time}`}`,`화면 주제: ${d.title}`,d.note??'',d.type==='section'?`차시별 자료: ${PERIODS[p].files}. 첫 실행은 강사가 보여주고, 학생은 Notebook 해당 차시에서 직접 코드를 수정한다.`:'',d.type==='task'?`학생 작업:\n${d.steps.map((s,i)=>`${i+1}. ${s}`).join('\n')}\n파일: ${d.file}\n성공 확인: ${d.check}`:'',d.type==='prompt'?'이 문구는 입력할 요청 예시이며 실제 모델 응답이 아니다. 계정·모델의 실행 가능 여부와 사용량을 먼저 확인한다.':'',d.type==='image'?`그림 출처: ${d.asset}\n실제 파일의 렌더 또는 명시된 브라우저 캡처. 서비스의 실행 여부를 이미지보다 넓게 주장하지 않는다.`:'','학습 방식: 온라인 개인 실행. 짝 활동·발표 의무 없음. 설치 지연은 제공 결과 파일로 설명을 이어가고, 실행 미완료를 완료로 표시하지 않는다.',`[Sources]\n${sources.join('\n')}\n[/Sources]`].filter(Boolean).join('\n\n');
 sl.speakerNotes.textFrame.setText(note);sl.speakerNotes.setVisible(true);
 manifest.push({page,period:p==null?1:p+1,title:d.title,type:d.type,phase:d.phase??'guide',minutes,reference:d.reference??false,expanded:d.expanded??false,activityLabel:d.activityLabel??null,asset:d.asset??null,notes:note,code:d.code??null});
}
const candidate=path.join(BUILD,'candidate.pptx');
await (await PresentationFile.exportPptx(deck)).save(candidate);
const layout=execFileSync(PYTHON,[path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),candidate,'--fail-on-findings','--expected-slide-count',String(plan.length),'--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit','--approved-font-family',FONT,'--approved-font-family',MONO,...tableOwners.flatMap(n=>['--require-native-table-slide',String(n)])],{encoding:'utf8'});
await fs.writeFile(path.join(BUILD,'all-native-table-validation.json'),layout);
await fs.mkdir(path.dirname(FINAL),{recursive:true});
const bounded=tableOwners.slice(0,35);
const receipt=await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath:FINAL,explicitTotalSlideCount:200,pythonExecutable:PYTHON,integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...bounded.flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:bounded,fontPolicy:{basis:'design',families:[FONT,MONO]},verifyArtifactToolImport:true,receiptPath:path.join(BUILD,path.basename(FINAL)+'.validation.json')});
await fs.writeFile(path.join(BUILD,'slide_manifest.json'),JSON.stringify(manifest,null,2));
const guide=['# 4주차 페이지별 강의 진행','',`총 ${plan.length}장 · 기본 학습 400분 · 선택 확장 ${manifest.filter(x=>x.reference).length}장. 시작 안내 5분은 1차시에 포함합니다.`, '', '| 차시 | 시간 | 페이지 | 기본 학습 |','|---|---|---:|---:|',...ranges.map((r,i)=>`| ${i+1}차시 | ${PERIODS[i].time} | ${r[0]}–${r[1]} | 50분${i===0?' (시작 안내 포함)':''} |`),'',...manifest.map(x=>`## ${x.page}. ${x.title}\n\n${x.notes}${x.code?'\n\n```text\n'+x.code+'\n```':''}`)].join('\n');
await fs.writeFile(path.join(ROOT,'materials/day4/페이지별_강의_진행.md'),guide);
await fs.writeFile(path.join(ROOT,'design-system/ppt/cha-sungjae-lecture/content-harness/DAY4_MESSAGE_MAP.json'),JSON.stringify({slideCount:plan.length,ranges,teachingMinutes:total,breakAndQAMinutes:80,lunchMinutes:60,fonts:{bodyPoint:22.5,tablePoint:19.5,codePoint:18,titlePoint:37.5},slides:manifest.map(({notes,code,...rest})=>rest)},null,2)+'\n');
console.log(JSON.stringify({pptx:FINAL,slides:plan.length,nativeTables:tableOwners.length,minutes:total,receipt},null,2));
