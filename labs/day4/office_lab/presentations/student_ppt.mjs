// Student reproduction with a public npm dependency.
// Run from the repository root. Source data and editable slides stay local.
import fs from 'node:fs/promises';
import path from 'node:path';
import pptxgen from 'pptxgenjs';

async function main() {
const root = await fs.realpath(process.cwd());
const source = process.argv[2] ?? 'labs/day4/office_lab/presentations/project_brief.json';
const target = process.argv[3] ?? 'outputs/day4-document-automation/Project_Brief_student.pptx';

async function insideWorkspace(file, writing = false) {
  const absolute = path.resolve(root, file);
  // Resolve an existing ancestor before creating directories, including symlinks.
  let ancestor = writing ? path.dirname(absolute) : absolute;
  const tail = writing ? [path.basename(absolute)] : [];
  while (true) {
    try { ancestor = await fs.realpath(ancestor); break; }
    catch (error) {
      if (error.code !== 'ENOENT' || ancestor === path.dirname(ancestor)) throw error;
      tail.unshift(path.basename(ancestor)); ancestor = path.dirname(ancestor);
    }
  }
  const resolved = path.resolve(ancestor, ...tail);
  const relative = path.relative(root, resolved);
  if (relative.startsWith('..' + path.sep) || relative === '..' || path.isAbsolute(relative)) throw new Error('PATH_OUTSIDE_WORKSPACE');
  return resolved;
}

const inputPath = await insideWorkspace(source);
const outputPath = await insideWorkspace(target, true);
if (path.extname(outputPath).toLowerCase() !== '.pptx') throw new Error('INVALID_OUTPUT_EXTENSION');
const data = JSON.parse(await fs.readFile(inputPath, 'utf8'));
if (data.schema_version !== 1 || !Array.isArray(data.slides) || data.slides.length !== 7) throw new Error('BRIEF_SCHEMA_INVALID');
const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = '';
pptx.subject = data.project;
pptx.title = data.project;
pptx.lang = 'ko-KR';
pptx.theme = {headFontFace: 'NanumGothic', bodyFontFace: 'NanumGothic', lang: 'ko-KR'};
for (const [index, content] of data.slides.entries()) {
  const slide = pptx.addSlide();
  slide.background = {color: index === 0 ? '111111' : 'FFFFFF'};
  const color = index === 0 ? 'FFFFFF' : '111111';
  slide.addText(content.title, {x:.6,y:index===0?1.5:.45,w:12.1,h:index===0?1.65:.65,fontSize:index===0?42:30,bold:true,color,margin:0,breakLine:false});
  if(content.subtitle) slide.addText(content.subtitle, {x:.6,y:index===0?3.6:1.22,w:12.1,h:.45,fontSize:20,color,margin:0});
  if(index===0)slide.addText('수업용 프로젝트',{x:.6,y:5.6,w:12.1,h:.5,fontSize:22,color,margin:0});
  if(content.table) {
    const widths = content.table[0].length===4 ? [5.3,2.4,1.7,1.7] : index===4 ? [1.1,4.5,6.5] : index===1 ? [2.2,1.9,8.0] : [2.6,4.2,5.3];
    const rows=content.table.map((row,r)=>row.map(text=>({text,options:{bold:r===0,color:r===0?'FFFFFF':'111111',fill:r===0?'111111':r%2===0?'F4F4F4':'FFFFFF'}})));
    slide.addTable(rows, {x:.6,y:1.95,w:12.1,h:content.table.length>5?4.96:3.7,colW:widths,fontSize:22,fontFace:'NanumGothic',color:'111111',margin:.12,border:{type:'solid',color:'D9D9D9',pt:1},fill:'FFFFFF',rowH:.62,bold:false,autoPage:false});
  }
  if(content.bullets) content.bullets.forEach((text, i)=>slide.addText(text,{x:.8,y:2+i*.8,w:11.8,h:.65,fontSize:25,color,margin:0,bullet:{indent:23},hanging:5,paraSpaceAfterPt:10}));
  slide.addNotes([content.note ?? '', '출처: '+data.sources.join(', '), '수업용 합성 프로젝트. 실제 회사 보고서가 아닙니다.']);
}
await fs.mkdir(path.dirname(outputPath), {recursive:true});
const handle = await fs.open(outputPath,'wx');
try { await handle.writeFile(await pptx.write({outputType:'nodebuffer'})); }
finally { await handle.close(); }
console.log(JSON.stringify({status:'CREATED',path:outputPath,slides:data.slides.length,review:'Open every slide before sharing.'}));
}

try { await main(); }
catch(error) {
  const known = new Set(['PATH_OUTSIDE_WORKSPACE','INVALID_OUTPUT_EXTENSION','BRIEF_SCHEMA_INVALID']);
  const code = known.has(error.message) ? error.message : error.code==='EEXIST' ? 'OUTPUT_EXISTS' : error.code==='ENOENT' ? 'INPUT_OR_DIRECTORY_MISSING' : 'PPT_BUILD_FAILED';
  console.error(JSON.stringify({status:'ERROR',error:code}));
  process.exitCode = 2;
}
