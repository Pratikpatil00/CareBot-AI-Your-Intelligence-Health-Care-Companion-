"""Prepare the ONE root .env without overwriting keys or existing values."""
from pathlib import Path
import secrets
root=Path(__file__).resolve().parents[1]
path=root/'.env'
if not path.exists(): path.write_text((root/'.env.example').read_text(),encoding='utf-8')
lines=path.read_text(encoding='utf-8').splitlines()
found=False
for i,line in enumerate(lines):
    if line.startswith(('GROQ_API_KEY=YOUR_', 'MAPPLS_API_KEY=YOUR_')):
        lines[i]=line.split('=',1)[0]+'='
    if line.startswith('JWT_SECRET='):
        found=True
        if not line.split('=',1)[1].strip(): lines[i]='JWT_SECRET='+secrets.token_urlsafe(48)
if not found: lines.append('JWT_SECRET='+secrets.token_urlsafe(48))
if not any(line.startswith('MAPPLS_API_KEY=') for line in lines): lines.append('MAPPLS_API_KEY=')
path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Root .env prepared. Add your Groq and Mappls keys, then run python run.py.')
