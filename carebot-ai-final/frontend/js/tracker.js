initPage('tracker','Health Tracker','Log and review your vitals over time');
let chart;
async function loadReadings(){
 const entries=(await apiFetchVitals()).reverse();
 document.getElementById('entriesBody').innerHTML=entries.slice(-20).reverse().map(e=>`<tr><td>${escapeHTML(displayDate(e.timestamp))}</td><td>${e.bp_systolic??'—'} mmHg</td><td>${e.heart_rate??'—'} bpm</td></tr>`).join('')||'<tr><td colspan="3">No readings recorded yet.</td></tr>';
 if(typeof Chart==='undefined')return;
 const data={labels:entries.map(e=>new Date(e.timestamp).toLocaleDateString()),datasets:[{label:'Systolic BP',data:entries.map(e=>e.bp_systolic),borderColor:'#4F46E5',tension:.3},{label:'Heart rate',data:entries.map(e=>e.heart_rate),borderColor:'#F0872F',tension:.3}]};
 if(chart){chart.data=data;chart.update();}else chart=new Chart(document.getElementById('trackerChart'),{type:'line',data,options:{scales:{x:{grid:{display:false}},y:{grid:{color:'#E7E6F6'}}}}});
}
document.getElementById('saveBtn').onclick=e=>busy(e.currentTarget,async()=>{
 const bp=document.getElementById('bpInput').value.trim(),hr=document.getElementById('hrInput').value.trim();
 if(!bp&&!hr)throw new Error('Enter at least one reading.');
 await apiLogVital({bp_systolic:bp?Number(bp):null,heart_rate:hr?Number(hr):null});
 document.getElementById('bpInput').value='';document.getElementById('hrInput').value='';await loadReadings();notify('Reading saved.');
});
sessionReady.then(loadReadings).catch(e=>notify(e.message,true));
