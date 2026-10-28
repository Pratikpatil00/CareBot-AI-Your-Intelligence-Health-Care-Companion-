"""Check local OCR and Groq model access without printing keys or sending health data."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.config import Config
import pytesseract,requests

def main():
    if Config.TESSERACT_CMD:pytesseract.pytesseract.tesseract_cmd=Config.TESSERACT_CMD
    try:print('Tesseract:',pytesseract.get_tesseract_version())
    except Exception:print('Tesseract unavailable: install it or set TESSERACT_CMD.')
    if not Config.GROQ_API_KEY:print('Groq: missing GROQ_API_KEY.');return 1
    try:
        r=requests.get('https://api.groq.com/openai/v1/models',headers={'Authorization':'Bearer '+Config.GROQ_API_KEY},timeout=20)
        if not r.ok:print('Groq rejected model-list request, HTTP',r.status_code);return 1
        available={m['id'] for m in r.json()['data']}
        for kind,model in [('text',Config.GROQ_MODEL),('vision',Config.GROQ_VISION_MODEL)]:print(f'Groq {kind} model {model}:', 'available' if model in available else 'not available to this key')
    except (requests.RequestException,ValueError,KeyError):print('Groq connection/response failed.');return 1
    print('Mappls Web SDK key:', 'configured; verify domain restrictions/API access in the browser' if Config.MAPPLS_API_KEY else 'missing')
    return 0
if __name__=='__main__':raise SystemExit(main())
