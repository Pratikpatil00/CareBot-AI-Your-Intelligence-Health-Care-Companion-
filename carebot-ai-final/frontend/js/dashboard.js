initPage('dashboard','Good to see you',"Here's where your health stands today");
const FEATURE_STRIP=[
 {icon:'💬',tone:'purple',label:'Smart Conversations',desc:'Context-aware, patient-friendly answers.',href:'chat.html'},
 {icon:'📄',tone:'blue',label:'Report Analysis',desc:'OCR + plain-language explanations.',href:'reports.html'},
 {icon:'🩻',tone:'green',label:'X-Ray Insights',desc:'Educational image observations.',href:'xray.html'},
 {icon:'⏰',tone:'orange',label:'Smart Reminders',desc:'Review medicines and log doses.',href:'medicine.html'},
 {icon:'📊',tone:'indigo',label:'Health Trends',desc:'Track vitals and history over time.',href:'tracker.html'}
];
document.getElementById('moduleGrid').innerHTML=FEATURE_STRIP.map(f=>`<a href="${f.href}" style="text-decoration:none;color:inherit;" class="panel hover-lift module-card"><div style="display:flex;justify-content:center;margin-bottom:10px;"><div class="icon-badge ${f.tone}" style="width:44px;height:44px;font-size:19px;">${f.icon}</div></div><div class="module-title">${f.label}</div><div class="module-desc">${f.desc}</div></a>`).join('');
(async()=>{try{
 const user=await sessionReady;document.querySelector('#topbar-root h1').textContent=`Good to see you, ${user.name.split(' ')[0]}`;
 const d=await api('/dashboard'); if(d.bmi)document.querySelector('#topbar-root p').textContent+=` · BMI ${d.bmi}`; const values=document.querySelectorAll('.stat-value'),notes=document.querySelectorAll('.trend-arrow');
 values[0].innerHTML=`${d.latest.bp_systolic??'—'} <span class="unit">mmHg</span>`;
 values[1].innerHTML=`${d.latest.heart_rate??'—'} <span class="unit">bpm</span>`;
 values[2].innerHTML=`${d.water.today_total_ml}<span class="unit">/${d.water.daily_target_ml} mL</span>`;
 values[3].innerHTML=`${d.adherence_percent??'—'}<span class="unit">%</span>`;
 ['Latest recorded systolic reading','Latest recorded heart rate','Today, in your profile timezone','Today’s scheduled doses logged as taken'].forEach((x,i)=>notes[i].textContent=x);
 document.getElementById('remindersList').innerHTML=d.schedule.map(x=>`<div class="reminder-item"><div class="icon-badge green" style="width:36px;height:36px;font-size:16px;">💊</div><div><div class="r-label">${escapeHTML(x.name)} ${escapeHTML(x.dosage)}</div><div class="r-time">${escapeHTML(x.scheduled_time)} · ${escapeHTML(x.status)}</div></div></div>`).join('')||'<p>No medicines scheduled. Add them in Medicine Manager.</p>';
 if(typeof Chart==='undefined')throw new Error('Charts could not load. Check your internet/CDN access; your saved data is still available in Health Tracker.');
 new Chart(document.getElementById('vitalsChart'),{type:'line',data:{labels:d.vitals.map(v=>new Date(v.timestamp).toLocaleDateString()),datasets:[{label:'Systolic BP',data:d.vitals.map(v=>v.bp_systolic),borderColor:'#4F46E5',backgroundColor:'rgba(79,70,229,0.15)',fill:true,tension:.35,pointRadius:0},{label:'Heart rate',data:d.vitals.map(v=>v.heart_rate),borderColor:'#F0872F',tension:.35,pointRadius:0}]},options:{plugins:{legend:{labels:{font:{family:'Inter'}}}},scales:{x:{grid:{display:false}},y:{grid:{color:'#E7E6F6'}}}}});
 }catch(e){notify(e.message,true);}})();
