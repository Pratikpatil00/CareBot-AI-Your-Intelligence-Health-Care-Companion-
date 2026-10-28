initPage('hospital','Hospital Finder','Nearby healthcare with MapmyIndia / Mappls');
document.getElementById('mapSearch').value=new URLSearchParams(location.search).get('specialty')||'';
let healthcareMap,origin=null,nearbyPlugin,directionPlugin,detailPlugin,locationMarker;
let locationChoices=[],places=[],searchVersion=0,detailVersion=0;
const list=document.getElementById('placesList'),routeBox=document.getElementById('routeSummary');
const providerHelp='Check that your Mappls Web SDK key has the required APIs enabled and this domain is allowed.';
function loadMapScript(url){
  return new Promise((resolve,reject)=>{
    const script=document.createElement('script');let settled=false;
    const timer=setTimeout(()=>finish(new Error('Mappls did not load. Check your connection and key permissions.')),20000);
    function finish(error){if(settled)return;settled=true;clearTimeout(timer);error?reject(error):resolve();}
    script.src=url;script.onload=()=>finish();script.onerror=()=>finish(new Error(`Unable to load Mappls. ${providerHelp}`));document.head.append(script);
  });
}
function sdkResult(invoke){
  return new Promise((resolve,reject)=>{
    let settled=false;
    const timer=setTimeout(()=>done({error:'timeout'}),20000);
    function done(data){
      if(settled)return;settled=true;clearTimeout(timer);
      if(!data||data.error||Number(data.responseCode)>=400){reject(new Error(`Mappls request failed. ${providerHelp}`));return;}
      resolve(data);
    }
    try{invoke(done);}catch(e){clearTimeout(timer);reject(new Error(`Mappls request could not start. ${providerHelp}`));}
  });
}
// SDK callbacks can provide a place array or a REST response envelope.
function placeRows(data){
  if(Array.isArray(data))return data;
  if(Array.isArray(data?.suggestedLocations))return data.suggestedLocations;
  if(Array.isArray(data?.results))return data.results;
  if(data?.data)return placeRows(data.data);
  if(data?.eLoc||data?.mapplsPin||data?.placeName)return [data];
  return [];
}
function pinFor(place){return place.eLoc||place.mapplsPin||place.eloc||place.poiId||'';}
function coordinateFor(place){
  if(place.latitude===undefined||place.longitude===undefined||place.latitude===''||place.longitude==='')return null;
  const lat=Number(place.latitude),lng=Number(place.longitude);
  return Number.isFinite(lat)&&Number.isFinite(lng)&&Math.abs(lat)<=90&&Math.abs(lng)<=180?[lat,lng]:null;
}
function positionFor(place){return pinFor(place)||coordinateFor(place);}
function positionString(position){return Array.isArray(position)?position.join(','):position;}
function clearPlugin(plugin){try{if(plugin?.remove)plugin.remove();else plugin?.markers?.()?.remove?.();}catch{}}
function placeHTML(p){
  const rich=p.richInfo||{},rating=p.rating??rich.rating,open=p.openNow??p.open_now??rich.openNow;
  return `<h3>${escapeHTML(p.placeName||p.name||'Healthcare facility')}</h3><p>${escapeHTML(p.placeAddress||p.address||'Address not supplied')}</p><p>Rating: ${escapeHTML(rating??'Not supplied by Mappls')} · ${open===true?'Open now':open===false?'Closed now':'Opening status not supplied'}</p>`;
}
async function initializeMap(){
  const config=await api('/maps/config');
  const key=encodeURIComponent(config.api_key);
  await loadMapScript(`https://sdk.mappls.com/map/sdk/web?v=3.0&access_token=${key}`);
  await loadMapScript(`https://sdk.mappls.com/map/sdk/plugins?v=3.0&access_token=${key}&libraries=nearby,search,direction,getPinDetails`);
  if(!window.mappls?.Map)throw new Error(`Mappls SDK unavailable. ${providerHelp}`);
  healthcareMap=new mappls.Map('map',{center:{lat:22.9734,lng:78.6569},zoom:4});
  await new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>reject(new Error(`Map tiles did not load. ${providerHelp}`)),20000);
    healthcareMap.addListener('load',()=>{clearTimeout(timer);resolve();});
  });
  list.textContent='Choose “Use my location” or search for a city/address to find nearby healthcare.';
}
const mapReady=sessionReady.then(initializeMap);
mapReady.catch(e=>{list.textContent=e.message;notify(e.message,true);});
async function setOrigin(position,label){
  origin=position;document.getElementById('searchLocation').textContent=`Search location: ${label}`;
  clearPlugin(directionPlugin);routeBox.replaceChildren();
  clearPlugin(locationMarker);
  if(Array.isArray(position)){
    healthcareMap.setCenter({lat:position[0],lng:position[1]});healthcareMap.setZoom(13);
    locationMarker=new mappls.Marker({map:healthcareMap,position:{lat:position[0],lng:position[1]}});
  }
  await searchNearby();
}
async function searchNearby(){
  await mapReady;
  if(!origin)throw new Error('Choose your location or a city/address first.');
  const version=++searchVersion;
  clearPlugin(nearbyPlugin);list.textContent='Searching Mappls…';
  const category={hospital:'hospital',doctor:'clinic',pharmacy:'pharmacy'}[document.getElementById('mapType').value];
  const text=document.getElementById('mapSearch').value.trim();
  try{
    const result=await sdkResult(done=>{nearbyPlugin=mappls.nearby({map:healthcareMap,keywords:text||category,refLocation:origin,radius:Number(document.getElementById('mapRadius').value),fitbounds:true,geolocation:false,popup:false},done);});
    if(version!==searchVersion)return;
    places=placeRows(result);
    list.innerHTML=places.map((p,i)=>`<div class="feature-item">${placeHTML(p)}<button class="btn-outline" data-details="${i}">Details</button><button class="btn-outline" data-route="${i}">Directions</button></div>`).join('')||'<p>No nearby results. Try a larger radius or another search term.</p>';
  }catch(e){if(version===searchVersion)list.textContent=e.message;throw e;}
}
async function showDetails(p){
  const version=++detailVersion,box=document.getElementById('placeDetails');
  box.innerHTML=placeHTML(p);clearPlugin(detailPlugin);
  const pin=pinFor(p);
  if(!pin){box.insertAdjacentHTML('beforeend','<p>No Mappls PIN was supplied for additional details.</p>');return;}
  // Provider-managed details widget also shows fields available to the account's plan.
  const target=document.createElement('div');target.id='mapplsPlaceDetails';box.append(target);
  const result=await sdkResult(done=>{detailPlugin=mappls.getPinDetails({map:healthcareMap,pin,divId:'mapplsPlaceDetails',infoDiv:false,markerPopup:false,fitbounds:true},done);});
  if(version!==detailVersion)return;
  const enriched=placeRows(result)[0];
  if(enriched){const summary=document.createElement('div');summary.innerHTML=placeHTML({...p,...enriched});box.prepend(summary);}
}
async function showDirections(p){
  await mapReady;
  const end=positionFor(p);if(!origin||!end)throw new Error('Mappls did not supply a routable location for this place.');
  clearPlugin(directionPlugin);routeBox.innerHTML='<h3>Directions</h3><div id="mapplsDirections"></div>';
  await sdkResult(done=>{directionPlugin=mappls.direction({map:healthcareMap,start:positionString(origin),end:positionString(end),divId:'mapplsDirections',resource:'route_adv',profile:'driving',search:false,geolocation:false,autoSubmit:true,fitbounds:true,steps:true,callback:done});});
}
document.getElementById('locateMe').onclick=e=>busy(e.target,async()=>{
  await mapReady;
  if(!navigator.geolocation)throw new Error('Geolocation is unavailable. Choose a city/address instead.');
  const result=await new Promise((resolve,reject)=>navigator.geolocation.getCurrentPosition(resolve,()=>reject(new Error('Location access was denied or unavailable. Allow it in browser settings or choose a city/address.')),{enableHighAccuracy:true,timeout:15000,maximumAge:60000}));
  await setOrigin([result.coords.latitude,result.coords.longitude],'Your current location');
});
document.getElementById('mapForm').onsubmit=e=>{e.preventDefault();busy(e.submitter,searchNearby);};
document.getElementById('addressForm').onsubmit=e=>{e.preventDefault();busy(e.submitter,async()=>{
  await mapReady;
  const query=document.getElementById('mapAddress').value.trim();
  const result=await sdkResult(done=>new mappls.search(query,{geolocation:false},done));
  locationChoices=placeRows(result).filter(positionFor);
  document.getElementById('addressChoices').innerHTML=locationChoices.map((p,i)=>`<div class="feature-item"><strong>${escapeHTML(p.placeName||query)}</strong><p>${escapeHTML(p.placeAddress||'')}</p><button class="btn-outline" data-location="${i}">Use this location</button></div>`).join('')||'<p>No matching location found.</p>';
});};
document.getElementById('addressChoices').onclick=e=>{const b=e.target.closest('[data-location]');if(b)busy(b,async()=>{const p=locationChoices[Number(b.dataset.location)];await setOrigin(positionFor(p),p.placeName||p.placeAddress);document.getElementById('addressChoices').replaceChildren();});};
list.onclick=e=>{const b=e.target.closest('button');if(!b)return;if(b.dataset.details!==undefined)busy(b,()=>showDetails(places[Number(b.dataset.details)]));if(b.dataset.route!==undefined)busy(b,()=>showDirections(places[Number(b.dataset.route)]));};
