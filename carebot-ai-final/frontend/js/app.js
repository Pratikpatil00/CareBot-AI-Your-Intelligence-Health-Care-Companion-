// ============================================================
// CareBot AI — Shared app shell logic
// Handles: login guard, sidebar rendering, topbar, account switcher.
// Included on every page (except index.html / login).
// ============================================================

let currentUser = null;
try { currentUser = JSON.parse(sessionStorage.getItem('carebot_user') || 'null'); } catch {}
const sessionReady = api('/auth/me').then(user => {
  currentUser=user; sessionStorage.setItem('carebot_user',JSON.stringify(user));
  const accounts=getAccounts().filter(a=>a.id!==user.id);
  localStorage.setItem('carebot_known_accounts',JSON.stringify([{...user,email:user.username},...accounts].slice(0,5)));
  renderAccountSwitcher();
  if(user.role==='admin'){
    const nav=document.querySelector('.sidebar-nav');
    if(nav)nav.innerHTML='<a class="nav-item active" href="admin.html"><span class="nav-icon">🛡</span>Administration</a>';
  }else startReminders();
  return user;
}).catch(e => { location.href='index.html'; throw e; });
function requireAuth() { return currentUser?.name || 'Patient'; }

function initials(name) {
  const parts = name.trim().split(/\s+/);
  return (parts[0]?.[0] || "?").toUpperCase() + (parts[1]?.[0] || "").toUpperCase();
}

function colorForName(name) {
  let sum = 0;
  for (let i = 0; i < name.length; i++) sum += name.charCodeAt(i);
  return AVATAR_COLORS[sum % AVATAR_COLORS.length];
}

function avatarHTML(name, size) {
  const color = colorForName(name || "?");
  return `<div class="avatar" style="width:${size}px;height:${size}px;font-size:${size * 0.38}px;
    background:linear-gradient(135deg, ${color}, ${color}CC);">${escapeHTML(initials(name))}</div>`;
}

function getAccounts() {
  try {const rows=JSON.parse(localStorage.getItem('carebot_known_accounts')||'[]');return rows.filter(x=>Number.isInteger(x.id)&&typeof x.name==='string'&&typeof x.email==='string');} catch {return [];}
}
function getActiveAccountId() { return currentUser?.id; }
async function switchAccount(id) { const selected=getAccounts().find(a=>a.id===Number(id)); if(selected && selected.id!==currentUser?.id) await logout(selected.name); }
async function logout(nextName = '') {
  try { await api('/auth/logout',{method:'POST'}); sessionStorage.clear(); if(nextName)sessionStorage.setItem('carebot_next_name',nextName); location.href='index.html'; }
  catch(e) { notify(e.message,true); }
}

/** Renders the sidebar (nav + account switcher) into #sidebar-root */
function renderSidebar(activePage) {
  const root = document.getElementById("sidebar-root");
  if (!root) return;

  const navHTML = MODULES_NAV.map((m) => `
    <a class="nav-item ${m.key === activePage ? "active" : ""}" href="${m.href}">
      <span class="nav-icon">${m.icon}</span>${m.label}
    </a>
  `).join("");

  root.innerHTML = `
    <div class="sidebar-brand">
      <div class="logo-badge">🤖</div>
      <span>CareBot AI</span>
    </div>
    <div class="sidebar-new-btn-wrap">
      <a href="chat.html?new=1" style="text-decoration:none;">
        <button class="btn-gradient" style="width:100%;font-size:13.5px;padding:10px 0;">+ New Conversation</button>
      </a>
    </div>
    <div class="sidebar-nav">${navHTML}</div>
    <div class="sidebar-footer" id="account-switcher-root"></div>
  `;

  renderAccountSwitcher();
}

/** Renders the Claude-style account switcher into #account-switcher-root */
function renderAccountSwitcher() {
  const root = document.getElementById("account-switcher-root");
  if (!root) return;

  const accounts = getAccounts();
  const activeId = getActiveAccountId();
  const active = accounts.find((a) => a.id === activeId) || accounts[0];
  if (!active) return;

  const rows = accounts.map((a) => `
    <div class="account-row ${a.id === activeId ? "active" : ""}" onclick="switchAccount('${a.id}')">
      ${avatarHTML(a.name, 28)}
      <div style="flex:1;min-width:0;">
        <div class="account-name">${escapeHTML(a.name)}</div>
        <div class="account-email">${escapeHTML(a.email)}</div>
      </div>
      ${a.id === activeId ? '<span style="color:var(--indigo);font-size:15px;">✓</span>' : ""}
    </div>
  `).join("");

  root.innerHTML = `
    <div class="account-popover" id="account-popover">
      <div class="popover-heading">ACCOUNTS</div>
      ${rows}
      <div class="account-divider"></div>
      <div class="account-action" onclick="logout()"><span style="width:28px;text-align:center;color:var(--indigo);">＋</span> Add another account</div>
      <div class="account-action" onclick="location.href='profile.html'"><span style="width:28px;text-align:center;">⚙</span> Settings</div>
      <div class="account-action logout" onclick="logout()"><span style="width:28px;text-align:center;">⏻</span> Log out</div>
    </div>
    <div class="account-trigger" id="account-trigger">
      ${avatarHTML(active.name, 32)}
      <div style="flex:1;min-width:0;">
        <div class="account-name">${escapeHTML(active.name)}</div>
        <div class="account-email">${escapeHTML(active.email)}</div>
      </div>
      <span style="color:var(--text-muted);font-size:11px;">▾</span>
    </div>
  `;

  const trigger = document.getElementById("account-trigger");
  const popover = document.getElementById("account-popover");
  trigger.addEventListener("click", (e) => {
    e.stopPropagation();
    popover.classList.toggle("open");
    trigger.classList.toggle("open");
  });
  document.addEventListener("click", () => {
    popover.classList.remove("open");
    trigger.classList.remove("open");
  });
}

/** Renders the topbar (title + subtitle) into #topbar-root */
function renderTopbar(title, subtitle) {
  const root = document.getElementById("topbar-root");
  if (!root) return;
  root.innerHTML = `
    <h1>${title}</h1>
    ${subtitle ? `<p>${subtitle}</p>` : ""}
  `;
}

/** Call this at the top of every protected page's script */
function initPage(activePage, title, subtitle) {
  const name = requireAuth();
  if (!name) return null;
  renderSidebar(activePage);
  renderTopbar(title, subtitle);
  const menu = document.createElement('button');
  menu.className='btn-outline mobile-menu';menu.textContent='☰ Menu';
  menu.onclick=()=>document.getElementById('sidebar-root').classList.toggle('open');
  document.getElementById('topbar-root').prepend(menu);
  return name;
}


async function requestReminderPermission() {
  if ('Notification' in window && Notification.permission==='default') {
    try { await Notification.requestPermission(); } catch { /* In-app reminders remain available. */ }
  }
}
async function enableReminders() {
  const permission=requestReminderPermission(); // Browser user gesture must not be lost to API awaits.
  await sessionReady;
  localStorage.setItem(`carebot_reminders_${currentUser.id}`,'on');
  await permission;
  notify('Reminders enabled while CareBot is open. In-app reminders do not require notification permission.');
  await checkReminders();
}
function reminder(key,text) {
  const storageKey=`carebot_notice_${currentUser.id}_${key}`;
  if(localStorage.getItem(storageKey))return;
  localStorage.setItem(storageKey,String(Date.now()));
  if('Notification' in window && Notification.permission==='granted') {
    try {new Notification('CareBot reminder',{body:text,tag:storageKey});} catch { /* Mobile browsers may require a push service; banner still works. */ }
  }
  if(!key.startsWith('water_'))notify(text);
}
function renderWaterReminder(state) {
  let banner=document.getElementById('water-reminder-banner');
  if(!state.due){if(banner)banner.remove();}
  else {
    if(!banner){
      banner=document.createElement('div');banner.id='water-reminder-banner';banner.className='panel reminder-banner';banner.setAttribute('role','status');
      banner.innerHTML='<strong>💧 Time for a water break</strong><p>Consider a drink if it fits your personal hydration plan.</p><div class="feature-row"><a href="water.html" class="btn-outline">Log water</a><button class="btn-outline" id="snoozeWater">Remind me in 10 minutes</button></div>';
      document.querySelector('.page-content')?.prepend(banner);
      banner.querySelector('button').onclick=e=>busy(e.target,async()=>{renderWaterReminder(await api('/water/reminder/snooze',{method:'POST'}));});
    }
    reminder(`water_${state.next_due_at}`,'Time for a water break. Log your drink in CareBot.');
  }
  const status=document.getElementById('waterReminderStatus');
  if(status)status.textContent=!state.enabled?'Water reminders are off. Save an interval of 1–240 minutes to turn them on.':state.goal_met?'Daily target reached. Reminders resume tomorrow.':state.due?'Water reminder is due now.':`Next reminder: ${displayDate(state.next_due_at)}. Keep CareBot open; sleeping devices may delay alerts.`;
}
let reminderChecking=false;
async function checkReminders() {
  if(!currentUser||currentUser.role==='admin'||reminderChecking)return;
  reminderChecking=true;
  try {
    renderWaterReminder(await api('/water/reminder'));
    if(localStorage.getItem(`carebot_reminders_${currentUser.id}`)==='on'){
      const doses=await api('/medicines/schedule');
      for(const d of doses)if(d.status==='due'&&d.reminder_enabled)reminder(`${d.medicine_id}_${d.scheduled_date}_${d.scheduled_time}`,`Medicine reminder: ${d.name} ${d.dosage} at ${d.scheduled_time}. Check your dose log before taking it.`);
    }
  }catch(e){const status=document.getElementById('waterReminderStatus');if(status)status.textContent=`Reminder check failed: ${e.message} Retrying automatically.`;}
  finally{reminderChecking=false;}
}
function startReminders() {
  checkReminders();setInterval(checkReminders,15000);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)checkReminders();});
  window.addEventListener('focus',checkReminders);
}
