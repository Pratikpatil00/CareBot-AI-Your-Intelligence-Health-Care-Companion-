// Executes actual page JS and Flask routes over a pipe. This is NOT a visual browser test.
const {JSDOM,VirtualConsole}=require('jsdom');
const vm=require('node:vm');
const {spawn}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),readline=require('node:readline');
const root=path.resolve(__dirname,'..');
const child=spawn(process.env.CAREBOT_TEST_PYTHON||'python',['-m','backend.tests.dom_bridge'],{cwd:root,stdio:['pipe','pipe','inherit']});
let next=0,csrf='',user=null;const pending=new Map();
readline.createInterface({input:child.stdout}).on('line',line=>{const r=JSON.parse(line);csrf=r.csrf||'';const resolve=pending.get(r.id);pending.delete(r.id);resolve(r);});
function rpc(req){return new Promise(resolve=>{const id=++next;pending.set(id,resolve);child.stdin.write(JSON.stringify({...req,id})+'\n');});}
function wait(check){return new Promise((resolve,reject)=>{const start=Date.now();const timer=setInterval(()=>{if(check()){clearInterval(timer);resolve();}else if(Date.now()-start>10000){clearInterval(timer);reject(new Error('DOM condition timed out'));}},20);});}
const errors=[];
async function load(name){
 const vc=new VirtualConsole();vc.on('jsdomError',e=>{if(!e.message.includes('navigation'))errors.push(e.message);});
 const dom=new JSDOM(fs.readFileSync(path.join(root,'frontend',name),'utf8'),{url:'http://localhost:5000/'+name,runScripts:'outside-only',virtualConsole:vc});
 const w=dom.window;w.confirm=()=>true;w.HTMLElement.prototype.scrollIntoView=()=>{};w.Chart=class{constructor(){}update(){}};
 if(user)w.sessionStorage.setItem('carebot_user',JSON.stringify(user));
 if(csrf)w.document.cookie='csrf_access_token='+csrf;
 w.fetch=async(url,opts={})=>{const result=await rpc({path:url,method:opts.method||'GET',body:opts.body?JSON.parse(opts.body):undefined,headers:opts.headers||{}});if(result.csrf)w.document.cookie='csrf_access_token='+result.csrf;return{ok:result.status>=200&&result.status<300,status:result.status,json:async()=>result.json};};
 for(const s of w.document.querySelectorAll('script[src]')){const src=s.getAttribute('src');if(!src.startsWith('http'))vm.runInContext(fs.readFileSync(path.join(root,'frontend',src),'utf8'),dom.getInternalVMContext(),{filename:src});}
 if(!['index.html','admin-login.html'].includes(name))await vm.runInContext('sessionReady',dom.getInternalVMContext());
 await wait(()=>pending.size===0);
 return dom;
}
function set(w,id,value){w.document.getElementById(id).value=value;}
function click(w,selector){w.document.querySelector(selector).click();}
(async()=>{
 let dom=await load('index.html'),w=dom.window;
 click(w,'#modeToggle');set(w,'nameInput','DOM Test Patient');set(w,'passwordInput','DOMPassword123!');set(w,'loginHeight','175');set(w,'loginWeight','70');w.document.getElementById('consentInput').checked=true;click(w,'#loginBtn');
 await wait(()=>w.sessionStorage.getItem('carebot_user'));user=JSON.parse(w.sessionStorage.getItem('carebot_user'));dom.window.close();
 assert.equal((await rpc({path:'/api/profile',method:'GET'})).json.data.height_cm,175);
 dom=await load('dashboard.html');w=dom.window;await wait(()=>w.document.querySelectorAll('.stat-value')[2].textContent.includes('2000'));dom.window.close();
 dom=await load('tracker.html');w=dom.window;set(w,'bpInput','121');set(w,'hrInput','75');click(w,'#saveBtn');await wait(()=>w.document.getElementById('entriesBody').textContent.includes('121'));dom.window.close();
 dom=await load('medicine.html');w=dom.window;await wait(()=>w.document.getElementById('medicineList').textContent.includes('No medicines'));
 set(w,'medicineName','DOM medicine');set(w,'medicineDosage','As prescribed');set(w,'medicineTimes','08:30');click(w,'#medicineForm button');await wait(()=>w.document.getElementById('medicineList').textContent.includes('DOM medicine'));
 click(w,'[data-status="taken"]');await wait(()=>w.document.getElementById('doseList').textContent.includes('taken'));dom.window.close();
 dom=await load('water.html');w=dom.window;await wait(()=>w.document.getElementById('waterSummary').textContent.includes('0 /'));click(w,'#waterForm button');await wait(()=>w.document.getElementById('waterSummary').textContent.includes('250 /'));
 set(w,'waterInterval','1');click(w,'#waterSettings button');await wait(()=>w.document.getElementById('waterReminderStatus').textContent.includes('Next reminder'));
 vm.runInContext("renderWaterReminder({due:true,enabled:true,next_due_at:'2026-01-01T00:00:00Z'})",dom.getInternalVMContext());
 assert(w.document.getElementById('water-reminder-banner'));click(w,'#snoozeWater');await wait(()=>!w.document.getElementById('water-reminder-banner'));click(w,'#testWaterReminder');assert.match(w.document.getElementById('app-notice').textContent,/Test reminder/);dom.window.close();
 dom=await load('profile.html');w=dom.window;await wait(()=>w.document.getElementById('timezone').value);set(w,'age','25');set(w,'weight_kg','70');set(w,'height_cm','175');click(w,'#profileForm button');await wait(()=>w.document.getElementById('bmiResult').textContent.includes('22.9'));dom.window.close();
 dom=await load('chat.html');w=dom.window;await wait(()=>w.document.getElementById('chatMessages').textContent.includes('CareBot'));set(w,'chatInput','Hello');click(w,'#sendBtn');await wait(()=>w.document.getElementById('chatMessages').textContent.includes('not configured'));dom.window.close();
 for(const page of ['reports','xray','specialist','symptoms','diet','hospital']){dom=await load(page+'.html');if(page==='hospital')await wait(()=>dom.window.document.getElementById('app-notice')?.textContent.includes('MAPPLS_API_KEY'));dom.window.close();}
 dom=await load('dashboard.html');w=dom.window;await wait(()=>w.document.querySelectorAll('.stat-value')[0].textContent.includes('121'));assert.match(w.document.querySelectorAll('.stat-value')[2].textContent,/250/);dom.window.close();
 dom=await load('admin.html');await wait(()=>dom.window.document.getElementById('app-notice')?.textContent.includes('Administrator access required'));assert.equal(dom.window.document.getElementById('patientList').textContent,'');dom.window.close();
 dom=await load('admin-login.html');w=dom.window;set(w,'nameInput','DOM Admin');set(w,'passwordInput','DOMAdminPassword123!');w.document.getElementById('consentInput').checked=true;click(w,'#loginBtn');
 await wait(()=>JSON.parse(w.sessionStorage.getItem('carebot_user'))?.role==='admin');user=JSON.parse(w.sessionStorage.getItem('carebot_user'));dom.window.close();
 dom=await load('admin.html');w=dom.window;await wait(()=>w.document.getElementById('patientList').textContent.includes('DOM Test Patient'));click(w,'[data-patient]');await wait(()=>w.document.getElementById('patientRecords')?.textContent.includes('121'));assert.match(w.document.getElementById('patientDetail').textContent,/175/);
 set(w,'recordKind','water');w.document.getElementById('recordKind').dispatchEvent(new w.Event('change'));await wait(()=>w.document.getElementById('patientRecords').textContent.includes('250'));dom.window.close();
 assert.deepEqual(errors,[]);console.log('DOM integration passed: all 15 pages, registration, persistent vitals, medicine/dose, water, profile/BMI, login measurements, water alerts/snooze, admin denial/login/patient records, dashboard, and explicit missing-key errors. Chart rendering and Mappls providers are not simulated as successes.');
 child.stdin.end();
})().catch(e=>{console.error(e);child.kill();process.exit(1);});
