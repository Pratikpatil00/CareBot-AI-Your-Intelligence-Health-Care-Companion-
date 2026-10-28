// Same-origin API: Flask serves both frontend and backend; no client secrets.
async function api(path, options = {}) {
  const {method = 'GET', body, signal, redirect = true} = options;
  const headers = {};
  if (body && !(body instanceof FormData)) headers['Content-Type'] = 'application/json';
  if (!['GET', 'HEAD'].includes(method)) {
    const csrf = document.cookie.split('; ').find(c => c.startsWith('csrf_access_token='));
    if (csrf) headers['X-CSRF-TOKEN'] = decodeURIComponent(csrf.split('=').slice(1).join('='));
  }
  let response;
  try {
    response = await fetch(`/api${path}`, {method, headers, credentials: 'same-origin', signal,
      body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined});
  } catch (e) {
    if (e.name === 'AbortError') throw e;
    throw new Error('Cannot reach CareBot. Start the server and check your connection.');
  }
  const data = await response.json().catch(() => null);
  if (!response.ok || !data?.success) {
    if (response.status === 401 && redirect && !location.pathname.endsWith('index.html') && location.pathname !== '/') {
      sessionStorage.removeItem('carebot_user'); location.href = 'index.html';
    }
    throw new Error(data?.message || `Request failed (${response.status}).`);
  }
  return data.data;
}
const apiSendChatMessage = (message, thread_id) => api('/assistant/chat', {method:'POST', body:{message,thread_id}});
const apiFetchVitals = () => api('/health/measurements?limit=200');
const apiLogVital = body => api('/health/measurements', {method:'POST',body});
function apiUploadReport(file) { const body=new FormData();body.append('file',file);return api('/reports/upload',{method:'POST',body}); }
function escapeHTML(value) { return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function displayDate(value) { return new Date(value).toLocaleString(); }
function notify(message, error = false) {
  let box = document.getElementById('app-notice');
  if (!box) { box=document.createElement('div');box.id='app-notice';box.className='info-callout';box.setAttribute('role','status');(document.querySelector('.page-content')||document.querySelector('.login-right')).prepend(box); }
  box.textContent=message;box.hidden=false;box.style.color=error?'#B23434':'';
}
async function busy(button, fn) {
  const text=button.textContent;button.disabled=true;button.textContent='Please wait…';
  try { return await fn(); } catch(e) { notify(e.message,true); } finally { button.disabled=false;button.textContent=text; }
}
function renderTextList(items) { return `<ul>${(items||[]).map(x=>`<li>${escapeHTML(x)}</li>`).join('')}</ul>`; }
