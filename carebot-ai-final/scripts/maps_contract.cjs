// Mappls SDK boundary fixtures only: validates wiring, not live provider access/rendering.
const {JSDOM}=require('jsdom'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
(async()=>{
 const dom=new JSDOM(fs.readFileSync(path.join(root,'frontend/hospital.html'),'utf8'),{url:'http://localhost:5000/hospital.html',runScripts:'outside-only'});
 const w=dom.window,ctx=dom.getInternalVMContext(),calls={};
 const run=s=>vm.runInContext(s,ctx);
 w.initPage=()=>{};w.sessionReady=Promise.resolve();
 w.fetch=async()=>({ok:true,json:async()=>({success:true,data:{api_key:'test-key',provider:'mappls'}})});
 const append=w.document.head.append.bind(w.document.head);
 w.document.head.append=node=>{append(node);if(node.tagName==='SCRIPT')setImmediate(()=>node.onload());};
 let result={suggestedLocations:[{eLoc:'ABC123',placeName:'<script>bad()</script>',placeAddress:'Test address'}]};
 w.mappls={
  Map:class{addListener(name,fn){setImmediate(fn);}setCenter(p){calls.center=p;}setZoom(){}},
  Marker:class{remove(){}},
  nearby(options,callback){calls.nearby=options;setImmediate(()=>callback(result));return{markers:()=>({remove(){}})};},
  search:class{constructor(query,options,callback){calls.search=query;setImmediate(()=>callback([{eLoc:'CITY01',placeName:'City name',placeAddress:'City address'}]));}},
  getPinDetails(options,callback){calls.details=options;setImmediate(()=>callback([{eLoc:'ABC123',placeName:'Clinic details',rating:4.1,openNow:false}]));return{remove(){}};},
  direction(options){calls.direction=options;setImmediate(()=>options.callback({routes:[{distance:1234}]}));return{remove(){}};}
 };
 for(const file of ['api.js','hospital.js'])run(fs.readFileSync(path.join(root,'frontend/js',file),'utf8'));
 await run('mapReady');
 await run("setOrigin([19.1,72.8],'Test location')");
 assert.equal(calls.nearby.radius,5000);assert.equal(calls.nearby.refLocation[0],19.1);
 assert(w.document.getElementById('placesList').textContent.includes('<script>'));
 assert.equal(w.document.getElementById('placesList').querySelector('script'),null);
 assert(w.document.getElementById('placesList').textContent.includes('Opening status not supplied'));
 await run('showDetails(places[0])');assert.equal(calls.details.pin,'ABC123');assert(w.document.getElementById('placeDetails').textContent.includes('Closed now'));
 await run('showDirections(places[0])');assert.equal(calls.direction.start,'19.1,72.8');assert.equal(calls.direction.end,'ABC123');assert.equal(calls.direction.divId,'mapplsDirections');
 w.document.getElementById('mapType').value='pharmacy';w.document.getElementById('mapRadius').value='10000';await run('searchNearby()');assert.equal(calls.nearby.keywords,'pharmacy');assert.equal(calls.nearby.radius,10000);
 await run("setOrigin('CITY01','Selected city')");assert.equal(calls.nearby.refLocation,'CITY01');
 result={error:'unauthorized'};await assert.rejects(run('searchNearby()'),/Mappls request failed/);
 result={suggestedLocations:[]};await run('searchNearby()');assert(w.document.getElementById('placesList').textContent.includes('No nearby results'));
 dom.window.close();console.log('Mappls contract checks passed: SDK loading, coordinates/PINs, categories/radius, escaped results, details, routing, empty/error states. Live Mappls is not tested.');
})().catch(e=>{console.error(e);process.exit(1);});
