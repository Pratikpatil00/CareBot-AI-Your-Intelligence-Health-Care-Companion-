const button=document.getElementById('loginBtn');
button.onclick=()=>busy(button,async()=>{
  const name=document.getElementById('nameInput').value.trim(),password=document.getElementById('passwordInput').value,consent=document.getElementById('consentInput').checked;
  if(!consent)throw new Error('Please confirm authorized access.');
  const user=await api('/auth/admin-login',{method:'POST',body:{name,password,consent},redirect:false});
  sessionStorage.setItem('carebot_user',JSON.stringify(user));location.href='admin.html';
});
document.getElementById('passwordInput').onkeydown=e=>{if(e.key==='Enter')button.click();};
