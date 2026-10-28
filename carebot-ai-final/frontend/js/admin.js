initPage('admin','Administration','Patient records · Administrator access only');
let patientPage=1,selectedPatient=null,recordPage=1,recordKind='measurements',searchGeneration=0,detailGeneration=0;
const detail=document.getElementById('patientDetail');
async function loadPatients(){
  document.getElementById('patientsPrev').disabled=true;document.getElementById('patientsNext').disabled=true;
  const generation=++searchGeneration;
  const data=await api(`/admin/patients?q=${encodeURIComponent(document.getElementById('patientQuery').value)}&page=${patientPage}`);
  if(generation!==searchGeneration)return;
  document.getElementById('patientCount').textContent=`${data.total} patient(s) · Page ${data.page}`;
  document.getElementById('patientList').innerHTML=data.items.map(u=>`<div class="feature-item"><strong>${escapeHTML(u.name)}</strong><p>Account #${u.id} · Joined ${escapeHTML(displayDate(u.created_at))}</p><button class="btn-outline" data-patient="${u.id}">View patient records</button></div>`).join('')||'<p>No patients found.</p>';
  document.getElementById('patientsPrev').disabled=patientPage===1;
  document.getElementById('patientsNext').disabled=!data.has_more;
}
function valueHTML(value){
  if(value===null||value===undefined||value==='')return 'Not provided';
  if(Array.isArray(value))return value.map(valueHTML).join('<br>')||'None';
  if(typeof value==='object')return `<dl>${Object.entries(value).map(([k,v])=>`<dt>${escapeHTML(k.replaceAll('_',' '))}</dt><dd>${valueHTML(v)}</dd>`).join('')}</dl>`;
  return escapeHTML(String(value));
}
async function selectPatient(id){
  const generation=++detailGeneration;selectedPatient=id;recordPage=1;recordKind='measurements';detail.hidden=false;detail.textContent='Loading patient…';
  const data=await api(`/admin/patients/${id}`);if(generation!==detailGeneration)return;
  detail.innerHTML=`<h2>${escapeHTML(data.user.name)}</h2><h3>Health profile</h3><div class="feature-result">${valueHTML(data.profile)}</div><label class="field-label">Records<select class="field-input" id="recordKind">${Object.entries(data.counts).map(([k,v])=>`<option value="${k}">${escapeHTML(k)} (${v})</option>`).join('')}</select></label><div id="patientRecords" class="feature-result"></div><div class="feature-row"><button class="btn-outline" id="recordsPrev">Previous records</button><button class="btn-outline" id="recordsNext">Next records</button></div>`;
  document.getElementById('recordKind').onchange=e=>{recordKind=e.target.value;recordPage=1;loadRecords().catch(e=>notify(e.message,true));};
  document.getElementById('recordsPrev').onclick=()=>{recordPage--;loadRecords().catch(e=>notify(e.message,true));};
  document.getElementById('recordsNext').onclick=()=>{recordPage++;loadRecords().catch(e=>notify(e.message,true));};
  await loadRecords();
}
let recordGeneration=0;
async function loadRecords(){
  document.getElementById('recordsPrev').disabled=true;document.getElementById('recordsNext').disabled=true;
  const generation=++recordGeneration,id=selectedPatient,kind=recordKind;
  const data=await api(`/admin/patients/${id}/records/${kind}?page=${recordPage}`);
  if(generation!==recordGeneration||id!==selectedPatient||kind!==recordKind)return;
  document.getElementById('patientRecords').innerHTML=data.items.map(x=>`<div class="feature-item">${valueHTML(x)}${kind==='documents'?`<a class="btn-outline" href="/api/admin/patients/${id}/documents/${x.id}/file">Download original</a>`:''}</div>`).join('')||'<p>No records yet.</p>';
  document.getElementById('recordsPrev').disabled=recordPage===1;document.getElementById('recordsNext').disabled=!data.has_more;
}
document.getElementById('patientSearch').onsubmit=e=>{e.preventDefault();patientPage=1;busy(e.submitter,loadPatients);};
document.getElementById('patientsPrev').onclick=()=>{patientPage--;loadPatients().catch(e=>notify(e.message,true));};
document.getElementById('patientsNext').onclick=()=>{patientPage++;loadPatients().catch(e=>notify(e.message,true));};
document.getElementById('patientList').onclick=e=>{const b=e.target.closest('[data-patient]');if(b)busy(b,()=>selectPatient(Number(b.dataset.patient)));};
sessionReady.then(user=>{if(user.role!=='admin'){detail.hidden=true;throw new Error('Administrator access required.');}return loadPatients();}).catch(e=>notify(e.message,true));
