initPage('profile','Profile Settings','Manage your saved health context');
let profile;
const fields=['age','gender','weight_kg','height_cm','known_conditions','preferences','allergies','timezone'];
async function load(){profile=await api('/profile');for(const key of fields)document.getElementById(key).value=profile[key]??'';document.getElementById('bmiResult').textContent=profile.bmi?`Calculated BMI: ${profile.bmi}. BMI is a limited screening measure, not a diagnosis.`:'Add height and weight to calculate BMI.';}
document.getElementById('profileForm').onsubmit=e=>{e.preventDefault();busy(e.submitter,async()=>{const p={...profile};delete p.bmi;for(const key of fields){const v=document.getElementById(key).value;p[key]=['age','weight_kg','height_cm'].includes(key)?(v?Number(v):null):v;}await api('/profile',{method:'PUT',body:p});await load();notify('Profile saved.');});};
sessionReady.then(load).catch(e=>notify(e.message,true));
