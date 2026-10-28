// Run against a disposable database: this creates an account and real test records.
const assert=require('node:assert/strict');
const path=require('node:path');
const fs=require('node:fs');
const output=path.resolve('test-results');fs.mkdirSync(output,{recursive:true});
const {chromium}=require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES ? path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright') : 'playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_EXECUTABLE_PATH||undefined});const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const base=process.env.CAREBOT_TEST_URL||'http://localhost:5010';
 await page.goto(base);await page.click('#modeToggle');
 await page.fill('#nameInput',`Browser Test ${Date.now()}`);await page.fill('#passwordInput','TestPassword123!');await page.check('#consentInput');
 await page.click('#loginBtn');await page.waitForURL('**/dashboard.html');await page.waitForFunction(()=>document.querySelectorAll('.stat-value')[2].textContent.includes('2000'));
 await page.screenshot({path:path.join(output,'dashboard.png'),fullPage:true});
 await page.goto(base+'/tracker.html');await page.fill('#bpInput','121');await page.fill('#hrInput','75');await page.click('#saveBtn');await page.waitForFunction(()=>document.querySelector('#entriesBody').textContent.includes('121'));
 await page.reload();await page.waitForFunction(()=>document.querySelector('#entriesBody').textContent.includes('121'));
 await page.goto(base+'/medicine.html');await page.fill('#medicineName','Browser Test Medicine');await page.fill('#medicineDosage','As prescribed');await page.fill('#medicineTimes','08:30');await page.locator('#medicineForm button').click();await page.waitForFunction(()=>document.querySelector('#medicineList').textContent.includes('Browser Test Medicine'));
 await page.locator('[data-dose][data-status="taken"]').click();await page.waitForFunction(()=>document.querySelector('#doseList').textContent.includes('taken'));
 await page.screenshot({path:path.join(output,'medicine.png'),fullPage:true});
 await page.goto(base+'/water.html');await page.locator('#waterForm button').click();await page.waitForFunction(()=>document.querySelector('#waterSummary').textContent.includes('250 /'));
 await page.goto(base+'/profile.html');await page.waitForFunction(()=>document.querySelector('#timezone').value.length>0);await page.fill('#age','25');await page.fill('#height_cm','175');await page.fill('#weight_kg','70');await page.locator('#profileForm button').click();await page.waitForFunction(()=>document.querySelector('#bmiResult').textContent.includes('22.9'));
 await page.goto(base+'/chat.html');await page.waitForFunction(()=>document.querySelector('#chatMessages').textContent.includes('CareBot'));await page.fill('#chatInput','Hello');await page.click('#sendBtn');await page.waitForFunction(()=>document.querySelector('#chatMessages').textContent.includes('not configured'));
 for(const name of ['reports','xray','specialist','symptoms','diet','hospital']){await page.goto(`${base}/${name}.html`);await page.waitForFunction(()=>document.querySelector('.account-trigger')!==null);}
 await page.waitForFunction(()=>document.querySelector('#app-notice').textContent.includes('MAPPLS_API_KEY'));
 await page.goto(base+'/dashboard.html');await page.waitForFunction(()=>document.querySelectorAll('.stat-value')[0].textContent.includes('121'));assert.match(await page.locator('.stat-value').nth(2).textContent(),/250/);
 await page.setViewportSize({width:800,height:1000});await page.locator('.mobile-menu').click();assert.equal(await page.locator('#sidebar-root').evaluate(x=>x.classList.contains('open')),true);
 assert.deepEqual(errors,[]);console.log('Browser smoke passed: registration, persistent vitals, medicine/dose, water, BMI, all pages, missing-key errors, dashboard and mobile navigation.');
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
