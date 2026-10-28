document.getElementById('nameInput').value=sessionStorage.getItem('carebot_next_name')||'';
let registering=false;
const mode=document.getElementById('modeToggle'),button=document.getElementById('loginBtn');
mode.onclick=e=>{e.preventDefault();registering=!registering;document.querySelector('.login-right h2').textContent=registering?'Create your account':'Welcome back';button.textContent=registering?'Create account and continue →':'Log in and continue →';mode.textContent=registering?'Already registered? Sign in':'New here? Create an account';document.getElementById('passwordInput').autocomplete=registering?'new-password':'current-password';};
button.onclick=()=>busy(button,async()=>{
  const name=document.getElementById('nameInput').value.trim(),password=document.getElementById('passwordInput').value,consent=document.getElementById('consentInput').checked;
  if(!name || password.length<8) throw new Error('Enter your full account name and a password with at least 8 characters.');
  if(!consent) throw new Error('Please review and accept the health-data consent to continue.');
  const user=await api(`/auth/${registering?'register':'login'}`,{method:'POST',body:{name,password,consent,height_cm:document.getElementById('loginHeight').value?Number(document.getElementById('loginHeight').value):null,weight_kg:document.getElementById('loginWeight').value?Number(document.getElementById('loginWeight').value):null},redirect:false});
  sessionStorage.setItem('carebot_user',JSON.stringify(user));location.href=user.role==='admin'?'admin.html':'dashboard.html';
});
document.getElementById('passwordInput').onkeydown=e=>{if(e.key==='Enter')button.click();};
