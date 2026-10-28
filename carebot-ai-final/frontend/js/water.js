initPage('water','Water Tracker','Track your daily hydration');
let waterProfile;
async function load(){const [p,s,logs]=await Promise.all([api('/profile'),api('/water/summary'),api('/water/logs')]);waterProfile=p;document.getElementById('waterTarget').value=p.water_target_ml;document.getElementById('waterInterval').value=p.water_reminder_minutes;document.getElementById('waterSummary').innerHTML=`<p><strong>${s.today_total_ml} / ${s.daily_target_ml} mL today (${s.today_progress_percent}%)</strong></p><p>Last 7 days: ${s.week_total_ml} mL · Daily average: ${s.week_average_ml} mL</p>`;document.getElementById('waterLogs').innerHTML=logs.map(x=>`<div class="feature-item">${x.amount_ml} mL · ${escapeHTML(displayDate(x.timestamp))} <button class="btn-outline" data-delete="${x.id}">Delete</button></div>`).join('')||'<p>No water logged yet.</p>';}
document.getElementById('waterForm').onsubmit=e=>{e.preventDefault();busy(e.submitter,async()=>{await api('/water/log',{method:'POST',body:{amount_ml:Number(document.getElementById('waterAmount').value)}});await load();await checkReminders();notify('Water intake saved.');});};
document.getElementById('waterSettings').onsubmit=e=>{e.preventDefault();busy(e.submitter,async()=>{const p={...waterProfile,water_target_ml:Number(document.getElementById('waterTarget').value),water_reminder_minutes:Number(document.getElementById('waterInterval').value)};delete p.bmi;await api('/profile',{method:'PUT',body:p});await load();await checkReminders();notify('Hydration settings saved. A nonzero interval enables in-app reminders automatically.');});};
document.getElementById('waterReminders').onclick=e=>{
  const permission=requestReminderPermission();
  busy(e.target,async()=>{
    await permission;
    if(!waterProfile)throw new Error('Wait for your hydration settings to load.');
    if(!waterProfile.water_reminder_minutes){const p={...waterProfile,water_reminder_minutes:60};delete p.bmi;await api('/profile',{method:'PUT',body:p});await load();}
    await enableReminders();
  });
};
document.getElementById('testWaterReminder').onclick=()=>{
  notify('Test reminder: your in-app water alerts are working.');
  if('Notification' in window&&Notification.permission==='granted'){try{new Notification('CareBot test reminder',{body:'Your water notifications are working.'});}catch{}}
};
document.getElementById('waterLogs').onclick=e=>{const b=e.target.closest('[data-delete]');if(b)busy(b,async()=>{await api(`/water/logs/${b.dataset.delete}`,{method:'DELETE'});await load();});};
sessionReady.then(load).catch(e=>notify(e.message,true));
