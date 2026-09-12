// Instructor build: the bundled Codex artifact runtime authors the reference PPT.
// Students use student_ppt.mjs with the public PptxGenJS package instead.
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const {RUNTIME_NODE_MODULES, RUNTIME_PYTHON, PRESENTATIONS_SKILL_DIR} = process.env;
for(const value of [RUNTIME_NODE_MODULES,RUNTIME_PYTHON,PRESENTATIONS_SKILL_DIR]) if(!path.isAbsolute(value??'')) throw new Error('BUNDLED_RUNTIME_REQUIRED');
const {Presentation,PresentationFile} = await import(pathToFileURL(path.join(RUNTIME_NODE_MODULES,'@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const {finalizePresentation,makeNativeBulletParagraphs}=await import(pathToFileURL(path.join(PRESENTATIONS_SKILL_DIR,'container_tools/artifact_tool_utils.mjs')).href);
const root=process.cwd();
const data=JSON.parse(await fs.readFile(path.join(root,'labs/day4/office_lab/presentations/project_brief.json'),'utf8'));
const out=path.join(root,'outputs/day4-document-automation');
const build=path.join(root,'.codex-work/day4-document-ppt');
await fs.mkdir(build,{recursive:true});
const deck=Presentation.create({slideSize:{width:1280,height:720}});
const font='NanumGothic';
function text(slide,str,x,y,w,h,size=32,color='#111111',bold=false){
  const box=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  box.text=str;
  box.text.style={typeface:font,fontSize:size,color,bold,autoFit:'none',wrap:true};
  return box;
}
for (const [index,content] of data.slides.entries()) {
  const slide=deck.slides.add();
  slide.background.fill=index===0?'#111111':'#FFFFFF';
  text(slide,content.title,60,index===0?144:38,1160,index===0?188:80,index===0?62:46,index===0?'#FFFFFF':'#111111',true);
  if(content.subtitle)text(slide,content.subtitle,60,index===0?382:120,1160,52,29,index===0?'#FFFFFF':'#111111');
  if(index===0)text(slide,'2026년 9월 14일 ~ 10월 9일\n수업용 프로젝트',60,520,1120,96,29,'#FFFFFF');
  if(content.table){
    const rows=content.table.length,columns=content.table[0].length;
    const widths=columns===4?[528,246,166,180]:index===4?[110,430,580]:index===1?[220,190,710]:[240,420,460];
    const height=rows>5?472:rows===3?366:432;
    const table=slide.tables.add({rows,columns,left:60,top:194,width:1120,height,columnWidths:widths,values:content.table});
    table.borders.assign({style:'solid',fill:'#D9D9D9',width:1});
    table.cells.block({row:0,column:0,rowCount:rows,columnCount:columns}).assign({fill:'#FFFFFF',textStyle:{typeface:font,fontSize:index===4?30:29,color:'#111111'},margins:{left:14,right:14,top:10,bottom:10},anchor:'center'});
    table.cells.block({row:0,column:0,rowCount:1,columnCount:columns}).assign({fill:'#111111',textStyle:{typeface:font,fontSize:29,color:'#FFFFFF',bold:true}});
    for(let r=1;r<rows;r++) if(r%2===0)table.cells.block({row:r,column:0,rowCount:1,columnCount:columns}).fill='#F4F4F4';
  }
  if(content.bullets){
    const box=text(slide,'',66,224,1140,430,34);
    box.text=makeNativeBulletParagraphs(content.bullets,{marginLeftPoints:24,hangingPoints:11,spaceAfterPoints:25});
  }
  slide.speakerNotes.textFrame.setText([content.note??'', '수업용 합성 프로젝트. 실제 회사 운영 현황이 아닙니다.', '입력 출처: '+data.sources.join(', '),'계산 기준일 '+data.as_of].join('\n'));
}
const candidate=path.join(build,'candidate.pptx');
await(await PresentationFile.exportPptx(deck)).save(candidate);
const final=path.join(out,process.argv[2]??'Project_Brief.pptx');
const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:final,pythonExecutable:RUNTIME_PYTHON,integrityValidatorPath:path.join(PRESENTATIONS_SKILL_DIR,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(PRESENTATIONS_SKILL_DIR,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...[2,3,4,5,6].flatMap(n=>['--require-native-table-slide',String(n)])],explicitTotalSlideCount:7,requiredNativeTableOwnerSlides:[2,3,4,5,6],fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,receiptPath:path.join(build,path.basename(final)+'.validation.json')});
for(let index=0;index<deck.slides.items.length;index++){
  const blob=await deck.export({slide:deck.slides.items[index],format:'png',scale:1});
  await fs.writeFile(path.join(build,`slide-${index+1}.png`),new Uint8Array(await blob.arrayBuffer()));
}
console.log(JSON.stringify(result));
