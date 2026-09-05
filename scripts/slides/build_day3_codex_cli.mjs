import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {Presentation, PresentationFile} from '@oai/artifact-tool';
import sharp from 'sharp';
import {execFileSync} from 'node:child_process';
import {OPENING, LESSONS, FUTURE, PERIODS} from './day3_ai_enrichment.mjs';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const SKILL='/Users/sungjae-cha/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations';
const PYTHON='/Users/sungjae-cha/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const FINAL=path.join(ROOT,'slides/IPA_LLM_Agent_업무자동화_Day3_2026_CODEX_CLI.pptx');
const STAGING=path.join(ROOT,'output/qa/day3-redesign/build');
process.env.RUNTIME_NODE_MODULES ??= await fs.realpath(path.join(ROOT,'node_modules'));
const C={ink:'#161616',paper:'#FFFFFF',muted:'#5B5B5B',line:'#DADADA',gray:'#F2F2F2',navy:'#0B1F3A'};
const S={title:54,section:62,body:30,table:26,code:24,label:24,footer:20};
const FONT='AppleGothic',MONO='Menlo';
const deck=Presentation.create({slideSize:{width:1280,height:720}});
const owners=[],manifest=[];
function shape(sl,geometry,x,y,w,h,fill='none',stroke='none'){
  return sl.shapes.add({geometry,position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width:stroke==='none'?0:1,style:'solid'}});
}
function txt(sl,text,x,y,w,h,{size=S.body,color=C.ink,bold=false,font=FONT,align='left',fill='none',middle=false}={}){
  const b=shape(sl,'textbox',x,y,w,h,fill); b.text=String(text??'');
  b.text.style={typeface:font,fontSize:size,color,bold,alignment:align,verticalAlignment:middle?'middle':'top',wrap:'square',autoFit:'none',lineSpacing:1.12,insets:{left:0,right:0,top:0,bottom:0}};
  return b;
}
function line(sl,x,y,w,color=C.line){shape(sl,'line',x,y,w,0,'none',color);}
function header(sl,title,p,page,label=null){
  sl.background.fill=C.paper;
  txt(sl,label??(p==null?'3주차 · 코드 리뷰 Agent':`3주차 ${p+1}차시 · ${PERIODS[p].time}`),64,28,1130,34,{size:S.label,bold:true,color:C.muted});
  txt(sl,title,64,84,1152,77,{size:S.title,bold:true});
  footer(sl,page);
}
function footer(sl,page,dark=false){
  const color=dark?'#C9C9C9':C.muted;
  line(sl,64,670,1152,dark?'#555555':C.line);
  txt(sl,'CODE REVIEW · CODEX CLI',64,684,800,26,{size:S.footer,color});
  txt(sl,String(page).padStart(3,'0'),1110,684,106,26,{size:S.footer,color,align:'right'});
}
function bullets(sl,items,x,y,w,{gap=100,size=S.body,color=C.ink}={}){
  items.forEach((item,i)=>{txt(sl,'·',x,y+i*gap,25,45,{size,color});txt(sl,item,x+32,y+i*gap,w-32,gap-12,{size,color});});
}
function table(sl,headers,rows,{x=64,y=188,w=1152,h=430,widths=null,size=S.table}={}){
  const values=[headers,...rows].map(row=>row.map(String));
  const tb=sl.tables.add({rows:values.length,columns:headers.length,left:x,top:y,width:w,height:h,values,columnWidths:widths??(headers.length===2?[w*.31,w*.69]:headers.length===3?[w*.25,w*.35,w*.4]:Array(headers.length).fill(w/headers.length))});
  tb.styleOptions={headerRow:true,bandedRows:false,firstColumn:false,lastColumn:false};
  tb.borders.assign({style:'solid',fill:C.line,width:1});
  const hh=60,rh=(h-hh)/rows.length;
  for(let r=0;r<values.length;r++){
    tb.rows[r].height=r===0?hh:rh;
    for(let c=0;c<headers.length;c++){
      const cell=tb.getCell(r,c);cell.fill=r===0?C.ink:r%2===0?C.gray:C.paper;
      cell.text.style={typeface:FONT,fontSize:size,bold:r===0||c===0,color:r===0?C.paper:C.ink,verticalAlignment:'middle',alignment:'left',wrap:'square',autoFit:'none',lineSpacing:1.08};
      tb.cells.block({row:r,column:c,rowCount:1,columnCount:1}).assign({margins:{left:16,right:14,top:10,bottom:10},anchor:'center'});
    }
  }
  owners.push(deck.slides.items.length);return tb;
}
function node(sl,label,x,y,w=250,h=84,dark=false){
  const sh=shape(sl,'rect',x,y,w,h,dark?C.navy:C.paper,dark?C.navy:C.ink);
  txt(sl,label,x+14,y+12,w-28,h-20,{size:26,bold:true,color:dark?C.paper:C.ink,align:'center',middle:true});
  return sh;
}
function arrow(sl,x,y,w=36,h=20){shape(sl,'rightArrow',x,y,w,h,C.ink);}
function down(sl,x,y){shape(sl,'downArrow',x,y,20,34,C.ink);}
function master(sl){
  const xs=[64,359,654,949],w=267;
  ['Git Diff\n検討할 변경'.replace('検討','검토'),'Context Pack\n업무 규칙·Test','Codex CLI + 모델\n제공된 코드 리뷰','Python 검증\n형식·라인·근거'].forEach((v,i)=>node(sl,v,xs[i],205,w,100,i===2));
  for(let i=0;i<3;i++)arrow(sl,xs[i]+w+5,245,22,18);
  down(sl,1071,313);
  node(sl,'LangGraph\n사람 검토 대기',949,358,w,100);
  node(sl,'Markdown 리뷰\n수용·수정·제외',654,358,w,100);
  shape(sl,'leftArrow',926,398,22,18,C.ink);
  node(sl,'학생 + 대화형 Codex\n코드 탐색·수정·Test',64,358,562,100,true);
  shape(sl,'leftArrow',630,398,22,18,C.ink);
  txt(sl,'반복',70,496,110,40,{size:26,bold:true});
  txt(sl,'수정 Diff와 테스트 결과로 다시 검토',196,496,850,45,{size:30});
  line(sl,64,555,1152);
  txt(sl,'4주차  GitHub PR 리뷰',64,581,550,48,{size:30,bold:true});
  txt(sl,'5주차  업무 통합·개인 서비스',652,581,565,48,{size:30,bold:true});
}
function human(sl){
  node(sl,'초안 검증',64,220,210,88);arrow(sl,285,253,48,22);
  node(sl,'interrupt\n사람 입력 대기',350,205,270,116,true);
  arrow(sl,635,253,48,22);node(sl,'같은 thread_id\nCommand로 재개',700,205,350,116);
  down(sl,867,330);
  const labels=['수용 → 보고서 준비','수정 → 내용 재검증','제외 → 이유 기록'];
  labels.forEach((v,i)=>node(sl,v,64+i*395,418,362,86));
  txt(sl,'미결정은 승인 아님 · 실제 GitHub 게시와 별도 단계',64,563,1152,60,{size:32,bold:true});
}
function futureflow(sl){
 const labels=['PR 이벤트','Diff 수집','리뷰 생성','사람 확인','PR 게시'];
 labels.forEach((v,i)=>{node(sl,v,64+i*235,225,211,105,i===3);if(i<4)arrow(sl,278+i*235,267,18,18);});
 table(sl,['문제','구현할 처리'],[['중복 이벤트','PR·Commit·리뷰 버전 기준 중복 방지'],['API 오류','재시도 횟수·대기 시간·실패 기록'],['권한과 게시','최소 권한·게시 미리보기·승인 확인']],{y:392,h:238,size:26});
}
function schedule(sl,half){
 const am=[['09:00-09:50','1차시','리뷰 대상과 업무 규칙'],['09:50-10:40','2차시','Git Diff와 재현 Test'],['10:40-11:30','3차시','리뷰 기준과 Context'],['11:30-12:00','쉬는 시간','오전 수업 후 30분'],['12:00-13:00','점심시간','13시 수업 시작']];
 const pm=[['13:00-14:40','4·5차시','CLI 연동·코드 수정'],['14:40-15:00','쉬는 시간','앞선 2차시 후 20분'],['15:00-17:30','6·7·8차시','검토 흐름·품질·서비스'],['17:30-18:00','쉬는 시간·Q&A','마지막 30분·실습 복구']];
 table(sl,['시간','구분','함께 챙길 내용'],half==='am'?am:pm,{widths:[300,295,557]});
}
function section(sl,p,page){
 sl.background.fill=C.ink;
 txt(sl,`3주차 ${p+1}차시`,64,55,1100,55,{size:32,bold:true,color:C.paper});
 txt(sl,PERIODS[p].time,64,138,1100,85,{size:68,bold:true,color:C.paper});
 txt(sl,PERIODS[p].title,64,251,1120,95,{size:62,bold:true,color:C.paper});
 txt(sl,PERIODS[p].goal,64,383,1115,64,{size:34,color:C.paper});
 const r=PERIODS[p];
 txt(sl,`이론 ${r.theory}분  ·  시연 ${r.demo}분  ·  코드 실습 ${r.lab}분  ·  확인 ${r.check}분`,64,550,1150,57,{size:30,color:C.paper});
 footer(sl,page,true);
}
async function render(d,p,page){
 const sl=deck.slides.add();
 if(d.type==='section'){section(sl,p,page);return sl;}
 if(d.type==='cover'){
  sl.background.fill=C.ink;txt(sl,'LLM AGENT & WORKFLOW AUTOMATION',64,58,1140,50,{size:28,color:C.paper});
  txt(sl,'03',64,172,370,190,{size:164,color:C.paper,bold:true});
  txt(sl,d.title,64,375,1152,100,{size:76,color:C.paper,bold:true});
  txt(sl,d.body,64,494,1100,65,{size:36,color:C.paper});
  txt(sl,'차성재 · Agentic AI PM / AI 겸임교수',64,594,1150,42,{size:28,color:C.paper});footer(sl,page,true);return sl;
 }
 header(sl,d.title,p,page,d.type==='closing'?'쉬는 시간·Q&A · 17:30-18:00':null);
 if(d.type==='table')table(sl,d.headers,d.rows,{widths:d.widths??null});
 else if(d.type==='schedule')schedule(sl,d.half);
 else if(d.type==='architecture')master(sl);
 else if(d.type==='humanflow')human(sl);
 else if(d.type==='futureflow')futureflow(sl);
 else if(d.type==='process'){
   d.steps.forEach((label,i)=>{
     const x=64+i*295;
     txt(sl,String(i+1).padStart(2,'0'),x,206,265,65,{size:44,bold:true,color:C.muted});
     node(sl,label,x,308,267,112,i===2);
     if(i<d.steps.length-1)arrow(sl,x+273,351,18,20);
   });
   txt(sl,d.detail,64,526,1152,96,{size:34,bold:true});
 }
 else if(d.type==='compare'){
   line(sl,64,246,552,C.ink);line(sl,664,246,552,C.ink);
   txt(sl,d.leftTitle,64,186,552,53,{size:34,bold:true});
   txt(sl,d.rightTitle,664,186,552,53,{size:34,bold:true});
   bullets(sl,d.left,64,282,552,{gap:104});bullets(sl,d.right,664,282,552,{gap:104});
 }else if(d.type==='code'){
   const lines=d.code.split('\n');
   const maxline=Math.max(...lines.map(l=>l.length));
   // Long commands get the full width. Concepts sit below rather than shrinking code.
   const wide=d.wide||maxline>50;
   shape(sl,'rect',64,190,wide?1152:795,wide?365:430,C.ink);
   txt(sl,d.code,86,212,wide?1108:750,wide?330:385,{size:S.code,font:MONO,color:C.paper});
   if(wide)txt(sl,d.explain.join('  /  '),64,581,1152,70,{size:27});
   else bullets(sl,d.explain,899,207,318,{gap:123,size:28});
 }else if(d.type==='conversation'){
   txt(sl,'요청',64,186,130,45,{size:28,bold:true});
   shape(sl,'rect',64,245,1152,245,C.gray);
   txt(sl,d.prompt,88,267,1104,214,{size:30});
   txt(sl,'응답 확인',64,535,180,45,{size:28,bold:true});
   txt(sl,d.check.join('  ·  '),257,535,950,90,{size:28});
 }else if(d.type==='task'){
   d.body.forEach((step,i)=>{
     txt(sl,String(i+1).padStart(2,'0'),64,202+i*106,94,65,{size:46,bold:true});
     txt(sl,step,179,204+i*106,1037,81,{size:32});
   });
   line(sl,64,545,1152);txt(sl,d.expected.join('  ·  '),64,574,1152,61,{size:29,bold:true});
 }else if(d.type==='demo'){
   txt(sl,d.body,64,189,1140,63,{size:32});
   txt(sl,d.leftLabel,64,300,535,48,{size:28,bold:true});txt(sl,d.rightLabel,685,300,532,48,{size:28,bold:true});
   txt(sl,d.leftValue,64,369,535,105,{size:74,bold:true});arrow(sl,599,408,53,25);
   txt(sl,d.rightValue,685,369,532,105,{size:74,bold:true});
   txt(sl,d.detail,64,549,1152,89,{size:30});
 }else if(d.type==='metrics'){
   txt(sl,d.body,64,183,1152,54,{size:30});
   d.values.forEach(([label,value],i)=>{const x=64+395*i;txt(sl,label,x,289,365,55,{size:32,bold:true});txt(sl,value,x,355,365,134,{size:96,bold:true});});
   txt(sl,d.detail,64,557,1152,62,{size:34,bold:true});
 }else if(d.type==='screenshot'){
   let buf=await fs.readFile(path.join(ROOT,d.asset));
   const maxHeight=d.caption?404:480;
   if(d.crop){
     // Retain an exact screenshot region for consistent PowerPoint/PDF display.
     // The unmodified full screenshot remains in assets for provenance.
     const sourceWidth=buf.readUInt32BE(16),sourceHeight=buf.readUInt32BE(20);
     const left=Math.round(sourceWidth*d.crop.left),top=Math.round(sourceHeight*d.crop.top);
     const width=sourceWidth-left-Math.round(sourceWidth*d.crop.right);
     const height=sourceHeight-top-Math.round(sourceHeight*d.crop.bottom);
     buf=await sharp(buf).extract({left,top,width,height}).png().toBuffer();
   }
   sl.images.add({blob:buf,contentType:'image/png',alt:'직접 실행한 로컬 코드 리뷰 서비스',fit:'contain',position:{left:64,top:174,width:1152,height:maxHeight}});
   if(d.caption)txt(sl,d.caption,64,595,1152,53,{size:30,bold:true});
 }else if(['concept','project_teaser','closing'].includes(d.type)){
   txt(sl,d.body,64,189,1152,110,{size:38,bold:true});
   bullets(sl,d.points,64,d.points.length>3?320:344,1130,{gap:d.points.length>3?78:94,size:32});
 }else throw new Error(`Unknown slide type ${d.type}`);
 if(d.source){
   const host=new URL(d.source).hostname.replace(/^www\./,'');
   txt(sl,`공식 참고 · ${host}`,64,638,1152,27,{size:20,color:C.muted});
 }
 return sl;
}
function distribute(items,total,p){
 const result=items.map(()=>0),core=items.map((d,i)=>({d,i})).filter(x=>x.d.delivery!=='reference');
 const checks=core.filter(x=>x.d.activity==='check');
 const labItems=core.filter(x=>x.d.lab);
 const check=checks.length?checks.at(-1):labItems.length>1?labItems.at(-1):core.filter(x=>x.d.type==='table').at(-1);
 if(check)result[check.i]=5;
 const practices=core.filter(x=>x.d.lab&&x!==check);
 const instructions=core.filter(x=>!x.d.lab&&x!==check);
 const practiceMinutes=PERIODS[p].lab;
 function allocate(group,minutes){
   if(!group.length&&minutes)throw new Error('Empty timing group');
   const weight=x=>x.d.type==='task'?5:x.d.type==='code'?2:x.d.type==='conversation'?2:x.d.type==='section'?.5:1;
   const weightSum=group.reduce((n,x)=>n+weight(x),0);
   group.forEach(x=>{result[x.i]=Math.max(.5,Math.floor(weight(x)/weightSum*minutes*2)/2);});
   let remain=minutes-group.reduce((n,x)=>n+result[x.i],0),i=0;
   const priority=[...group].sort((a,b)=>weight(b)-weight(a));
   while(remain>0){result[priority[i++%priority.length].i]+=.5;remain-=.5;}
   while(remain<0){const x=priority[i++%priority.length];if(result[x.i]>.5){result[x.i]-=.5;remain+=.5;}}
 }
 allocate(practices,practiceMinutes);
 allocate(instructions,total-practiceMinutes-(check?5:0));
 return result;
}
const plan=[];
const openingMinutes=new Map([[0,1],[1,1],[4,2],[5,3],[6,1],[7,1],[8,1]]);
OPENING.forEach((d,i)=>plan.push({d,p:null,minutes:openingMinutes.get(i)??0}));
const ranges=[];
LESSONS.forEach((items,p)=>{
 const all=[{type:'section',title:PERIODS[p].title},...items];
 const mins=distribute(all,p===0?40:p===7?41:50,p),start=plan.length+1;
 all.forEach((d,i)=>plan.push({d,p,minutes:mins[i]}));ranges.push([start,plan.length]);
});
FUTURE.forEach((d,i)=>plan.push({d,p:7,minutes:i===FUTURE.length-1?30:[2,1,2,2,1,1][i]??0}));
await fs.mkdir(STAGING,{recursive:true});
for(let i=0;i<plan.length;i++){
 const {d,p,minutes}=plan[i],page=i+1,sl=await render(d,p,page);
 const actions=d.type==='code'?`코드를 한 줄씩 실행하고 ${d.explain.join(', ')}를 확인합니다.`:d.type==='task'?d.body.map((x,j)=>`${j+1}. ${x}`).join('\n'):d.type==='conversation'?`요청을 Codex에 입력합니다. 답변 확인: ${d.check.join(', ')}.`:d.points?.join('\n')??d.rows?.map(x=>x.join(' / ')).join('\n')??d.body??'';
 const note=[`[강사용 진행]\n권장 시간: ${minutes}분${minutes===0?' (선택 설명·복습 참조, 기본 50분 미산정)':''}`,`차시: ${p==null?'시작 안내':`${p+1}차시 ${PERIODS[p].time}`}`,`설명 대상: ${d.title}`,d.note??'',actions,p!=null?`실습 연결: 정본 Notebook의 ${p+1}차시. 구체적 셀 번호와 파일은 수강생 실습가이드 및 페이지별 진행표 참조.`:'',`수업 방식: 온라인 개인 실행. 코드를 수정했다면 출력과 Test를 다시 확인. 의무 발표 없음. 선택 참고 장표는 설명 시간을 대체하거나 빠른 진행 시 사용하며 실습 시간을 잠식하지 않습니다.`,d.source?`[Sources]\n${d.source}\n[/Sources]`:''].filter(Boolean).join('\n\n');
 sl.speakerNotes.textFrame.setText(note);sl.speakerNotes.setVisible(true);
 manifest.push({page,period:p==null?null:p+1,title:d.title,type:d.type,minutes,delivery:minutes===0?'reference':'core',lab:d.lab??false,notes:note,...(d.source?{source:d.source}:{}),...(d.code?{code:d.code}:{}),...(d.asset?{asset:d.asset}:{})});
}
const candidate=path.join(STAGING,'candidate.pptx');await (await PresentationFile.exportPptx(deck)).save(candidate);
// The finalizer limits caller arguments to 96. Run the same immutable validator
// against every native-table owner first; keep finalizer arguments bounded.
const allTableValidation=execFileSync(PYTHON,[path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),candidate,'--fail-on-findings','--expected-slide-count',String(plan.length),'--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit','--approved-font-family',FONT,'--approved-font-family',MONO,...owners.flatMap(n=>['--require-native-table-slide',String(n)])],{encoding:'utf8'});
await fs.writeFile(path.join(STAGING,'all-native-table-validation.json'),allTableValidation);
const {finalizePresentation}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
await fs.mkdir(path.dirname(FINAL),{recursive:true});
const finalPath=process.env.DAY3_FINAL_PATH??FINAL;
const boundedOwners=owners.slice(0,40);
const validation=await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath,pythonExecutable:PYTHON,integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...boundedOwners.flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:boundedOwners,fontPolicy:{basis:'design',families:[FONT,MONO]},verifyArtifactToolImport:true,receiptPath:path.join(STAGING,`${path.basename(finalPath)}.validation.json`)});
await fs.writeFile(path.join(STAGING,'slide_manifest.json'),JSON.stringify(manifest,null,2));
const md=['# 3주차 페이지별 강의 진행','',`총 ${plan.length}장. 강의·시연·실습 400분, 마지막 휴식·Q&A 30분. 사전 참고 페이지는 0분으로 표시한다. 차시별 이론·시연·실습·확인 배분은 8개 차시 표지 기준이며, 아래 페이지 시간은 설명과 실행을 합친 진행 가이드다.`,...manifest.map(x=>`\n## ${x.page}. ${x.title}\n\n${x.notes}${x.code?'\n\n```python\n'+x.code+'\n```':''}`)].join('\n');
await fs.writeFile(path.join(ROOT,'materials/day3/페이지별_강의_진행.md'),md);
const map={deck:{path:path.relative(ROOT,FINAL),slideCount:plan.length,finalSynthesisSlides:[plan.length]},blocks:[{name:'시작 안내',range:[1,OPENING.length]},...ranges.map((range,i)=>({name:`3주차 ${i+1}차시`,range})),{name:'4·5주차와 미니 프로젝트',range:[plan.length-FUTURE.length+1,plan.length]}],slides:manifest.map(({notes,code,...rest})=>rest),timing:{teachingMinutes:400,lastBreakAndQAMinutes:30,openingMinutes:10,periodPageMinutes:[40,50,50,50,50,50,50,41],futurePreviewMinutes:9},design:{bodyPoint:22.5,tablePoint:19.5,codePoint:18,titlePoint:40.5},requiredNativeTables:owners};
await fs.writeFile(path.join(ROOT,'design-system/ppt/cha-sungjae-lecture/content-harness/DAY3_MESSAGE_MAP.json'),JSON.stringify(map,null,2)+'\n');
console.log(JSON.stringify({pptx:finalPath,slides:plan.length,nativeTables:owners.length,validation},null,2));
