initPage('reports','Report Analyzer','Upload a report for a plain-language explanation');
const uploadStage=document.getElementById('uploadStage'),processingStage=document.getElementById('processingStage'),doneStage=document.getElementById('doneStage'),fileInput=document.getElementById('fileInput');
let uploading=false;
function showStage(stage){uploadStage.style.display=stage==='upload'?'block':'none';processingStage.style.display=stage==='processing'?'block':'none';doneStage.style.display=stage==='done'?'block':'none';}
function showReport(doc){
 const r=doc.result;document.getElementById('doneFileName').textContent=doc.filename;document.getElementById('fieldCount').textContent=`Extracted ${r.fields.length} fields`;
 document.getElementById('reportFieldsBody').innerHTML=r.fields.map(f=>`<tr><td>${escapeHTML(f.field)}</td><td>${escapeHTML(f.value??'Unclear')} ${escapeHTML(f.unit)}</td><td>${escapeHTML(f.reference_range??'Not stated')}</td><td><span class="pill pill-indigo">${escapeHTML(f.status.replaceAll('_',' '))}</span></td></tr>`).join('');
 document.getElementById('reportExplanation').textContent=[r.explanation,...r.follow_up,...r.uncertainties,r.disclaimer].join('\n\n');document.getElementById('rawText').textContent=doc.extracted_text;showStage('done');
}
async function loadHistory(){const rows=await api('/documents?kind=report');document.getElementById('reportHistory').innerHTML=rows.map(r=>`<div class="feature-item"><button class="btn-outline" data-report="${r.id}">${escapeHTML(r.filename)}</button> <span>${escapeHTML(displayDate(r.created_at))}</span><a href="/api/documents/${r.id}/file" class="btn-outline">Original</a><button class="btn-outline" data-delete="${r.id}">Delete</button></div>`).join('')||'<p>No saved reports.</p>';}
async function handleUpload(file){
 if(!file||uploading)return;if(file.size>10*1024*1024)return notify('File must be under 10 MB.',true);
 uploading=true;document.getElementById('processingFileName').textContent=`Reading ${file.name}…`;showStage('processing');
 try{await sessionReady;showReport(await apiUploadReport(file));await loadHistory();}catch(e){notify(e.message,true);showStage('upload');}finally{uploading=false;fileInput.value='';}
}
uploadStage.onclick=e=>{if(e.target!==fileInput)fileInput.click();};fileInput.onchange=()=>handleUpload(fileInput.files[0]);
for(const event of ['dragenter','dragover'])uploadStage.addEventListener(event,e=>{e.preventDefault();uploadStage.classList.add('dragover');});
for(const event of ['dragleave','drop'])uploadStage.addEventListener(event,e=>{e.preventDefault();uploadStage.classList.remove('dragover');if(event==='drop')handleUpload(e.dataTransfer.files[0]);});
document.getElementById('uploadAnotherBtn').onclick=()=>showStage('upload');
document.getElementById('reportHistory').onclick=e=>{const b=e.target.closest('button');if(!b)return;busy(b,async()=>{if(b.dataset.report)showReport(await api(`/documents/${b.dataset.report}`));if(b.dataset.delete&&confirm('Delete this report and its uploaded file?')){await api(`/documents/${b.dataset.delete}`,{method:'DELETE'});showStage('upload');await loadHistory();}});};
sessionReady.then(loadHistory).catch(e=>notify(e.message,true));
