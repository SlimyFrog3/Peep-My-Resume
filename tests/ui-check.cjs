const fs = require('fs'), path = require('path'), assert = require('assert'), cp = require('child_process')
const { JSDOM } = require('jsdom')
const repo = path.resolve(__dirname, '..')
const ts = require(repo+'/node_modules/typescript')
const compiled = fs.mkdtempSync(path.join(repo, 'node_modules', '.ui-check-'))
function compile(dir) {
  for(const item of fs.readdirSync(dir,{withFileTypes:true})) {
    const file=path.join(dir,item.name)
    if(item.isDirectory()) compile(file)
    else if(/\.tsx?$/.test(file)&&!file.endsWith('.d.ts')) {
      const relative=path.relative(repo+'/src',file).replace(/\.tsx?$/,'.js')
      const output=path.join(compiled,relative); fs.mkdirSync(path.dirname(output),{recursive:true})
      fs.writeFileSync(output,ts.transpileModule(fs.readFileSync(file,'utf8').replaceAll('import.meta.env','({})'),{
        compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022}
      }).outputText)
    }
  }
}
compile(repo+'/src')
const dom=new JSDOM('<!doctype html><div id="root"></div>',{url:'https://test.local'})
global.window=dom.window;global.document=dom.window.document;global.navigator=dom.window.navigator
global.HTMLElement=dom.window.HTMLElement;global.HTMLDetailsElement=dom.window.HTMLDetailsElement
global.IS_REACT_ACT_ENVIRONMENT=true
dom.window.HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','')}
dom.window.HTMLDialogElement.prototype.close=function(){this.removeAttribute('open')}
let downloadedName='', downloadedBlob
dom.window.HTMLAnchorElement.prototype.click=function(){downloadedName=this.download}
URL.createObjectURL=b=>{downloadedBlob=b;return 'blob:test'}
URL.revokeObjectURL=()=>{}
const py=process.env.CODEX_PRIMARY_RUNTIME_PYTHON || process.env.PYTHON || 'python'
const bridge=`
import json,sys
from fastapi.testclient import TestClient
from backend.main import app
from backend.parser import group_sections
r=json.load(sys.stdin)
if r['path']=='fixture':
 print(json.dumps(group_sections('Taylor Example\\ntaylor@example.com\\nEXPERIENCE\\nQA Engineer | Sample Labs | 2022 - Present\\n- Built tests.\\nQA Analyst | Sample Systems | 2020 - 2022\\n- Reviewed releases.\\nSKILLS\\nPython, SQL\\nREFERENCES\\nAn important unplaced sentence.')))
else:
 with TestClient(app) as c:
  response=c.post(r['path'],json=r['body']) if r.get('body') else c.get(r['path'])
  print(json.dumps({'status':response.status_code,'body':response.json()}))
`
function api(path,body){return JSON.parse(cp.execFileSync(py,['-c',bridge],{cwd:repo,input:JSON.stringify({path,body}),stdio:['pipe','pipe','ignore'],encoding:'utf8'}))}
const calls=[]
let failSpacing=false
global.fetch=async(url,options={})=>{
 const pathname=new URL(url,'https://test.local').pathname; calls.push(pathname)
 const r=api(pathname,options.body?JSON.parse(options.body):undefined)
 if(failSpacing && pathname==='/review/preview') r.body.formattingCheck.passed=false
 return new Response(JSON.stringify(r.body),{status:r.status,headers:{'Content-Type':'application/json'}})
}
const React=require(repo+'/node_modules/react'), {act}=React
const {createRoot}=require(repo+'/node_modules/react-dom/client')
const Review=require(compiled+'/components/ResumeReview.js').default
const Score=require(compiled+'/components/ReadabilityScore.js').default
const result=api('fixture')
const root=createRoot(document.getElementById('root'))
function button(text){const found=[...document.querySelectorAll('button')].find(b=>b.textContent.trim()===text);assert(found,'Missing button: '+text);return found}
async function click(el){await act(async()=>{el.click();await new Promise(r=>setTimeout(r,10))})}
async function change(el,value){await act(async()=>{el.value=value;el.dispatchEvent(new dom.window.Event('change',{bubbles:true}));await new Promise(r=>setTimeout(r,5))})}
async function run(){
 await act(async()=>{root.render(React.createElement(Review,{result,demoMode:false}));await new Promise(r=>setTimeout(r,10))})
 assert(!document.body.textContent.includes('OpenAI'))
 await click(button('Review & create DOCX'));assert(document.querySelector('dialog[open]'))
 assert.equal(document.querySelectorAll('.template-card').length,3)
 await click([...document.querySelectorAll('.template-card')].find(b=>b.textContent.includes('Modern Accent')))
 assert(document.querySelector('.template-modern[aria-pressed=true]'))
 const skillsUp=document.querySelector('[aria-label="Move Skills section up"]')
 await click(skillsUp)
 let ordered=[...document.querySelectorAll('[data-edit-section]')].map(e=>e.dataset.editSection)
 assert(ordered.indexOf('skills')<ordered.indexOf('experience'))
 const jobIds=[...document.querySelectorAll('[data-edit-section=experience] [data-edit-block]')].map(e=>e.dataset.editBlock)
 await click(document.querySelector('[data-edit-section=experience] [aria-label="Move entry 1 down within Experience"]'))
 assert.deepEqual([...document.querySelectorAll('[data-edit-section=experience] [data-edit-block]')].map(e=>e.dataset.editBlock),jobIds.reverse())
 await click(button('Build preview & reparse DOCX'))
 assert(button('Download editable DOCX').disabled)
 assert(document.querySelector('.resume-style-modern'))
 assert(document.body.textContent.includes('Resolve its placement'))
 await click(button('1. Edit & choose style'))
 await click(button('Keep as Additional Information'))
 await click(button('Build preview & reparse DOCX'))
 const approved=[...document.querySelectorAll('input[type=checkbox]')].find(e=>e.parentElement.textContent.includes('approve this copy'))
 await click(approved)
 assert(!button('Download editable DOCX').disabled)
 const requestCount=calls.filter(p=>p==='/review/preview').length
 await click(button('Download editable DOCX'))
 assert.equal(downloadedName,'Peep-My-Resume-modern.docx')
 assert(downloadedBlob.size>1000)
 assert.equal(calls.filter(p=>p==='/review/preview').length,requestCount)
 const previewOrder=[...document.querySelectorAll('[data-resume-section]')].map(e=>e.dataset.resumeSection)
 assert(previewOrder.indexOf('skills')<previewOrder.indexOf('experience'))
 await click(button('1. Edit & choose style'))
 await click(document.querySelector('.template-compact'))
 await click(button('2. Preview & compare'))
 assert(![...document.querySelectorAll('button')].some(b=>b.textContent==='Download editable DOCX'))
 failSpacing=true
 await click(button('Build / refresh preview'))
 const reapprove=[...document.querySelectorAll('input[type=checkbox]')].find(e=>e.parentElement.textContent.includes('approve this copy'))
 await click(reapprove)
 assert(button('Download editable DOCX').disabled)
 assert(document.body.textContent.includes('Section spacing'))
 assert(!calls.some(p=>p.includes('/ai')))
 await act(async()=>{root.render(React.createElement(Score,{value:{...result.readability,score:98,status:'needs_review'}}))})
 assert(document.querySelector('.parse-check--needs_review'))
 assert(document.body.textContent.includes('What it takes to get green'))
 await act(async()=>{root.render(React.createElement(Score,{value:{...result.readability,score:54,status:'needs_attention'}}))})
 assert(document.querySelector('.parse-check--needs_attention'))
 await act(async()=>root.unmount())
 console.log(JSON.stringify({passed:true,checks:['template selection','section order','entry order','pending placement blocks download','explicit keep decision','approval','exact preview download','template invalidates approval','failed spacing blocks download','no AI calls','98 yellow explanation','54 red state']}))
}
run().catch(e=>{console.error(e);process.exitCode=1}).finally(()=>fs.rmSync(compiled,{recursive:true,force:true}))
