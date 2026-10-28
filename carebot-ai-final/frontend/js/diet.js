initPage('diet','Diet Planner','Personalized educational meal planning');
document.getElementById('dietGoal').value='A balanced daily eating plan';
function show(r){document.getElementById('dietResult').innerHTML=`<p>${escapeHTML(r.overview)}</p><h3>Meals</h3>${renderTextList(r.meals)}<h3>Considerations</h3>${renderTextList(r.considerations)}<p class="disclaimer">${escapeHTML(r.disclaimer)}</p>`;}
async function history(){const rows=(await api('/analyses')).filter(x=>x.kind==='diet'),root=document.getElementById('dietHistory');root.innerHTML='<div class="section-label">Saved plans</div>';for(const x of rows){const b=document.createElement('button');b.className='btn-outline';b.textContent=displayDate(x.created_at);b.onclick=()=>show(x.result);root.append(b);}}
document.getElementById('dietForm').onsubmit=e=>{e.preventDefault();busy(e.submitter,async()=>{const {result}=await api('/diet/plan',{method:'POST',body:{goal:document.getElementById('dietGoal').value}});show(result);await history();});};
sessionReady.then(history).catch(e=>notify(e.message,true));
