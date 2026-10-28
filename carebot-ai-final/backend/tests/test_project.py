from io import BytesIO
from datetime import datetime,timezone,timedelta
from uuid import uuid4
import json
import pytest
from PIL import Image,ImageDraw,ImageFont
from backend.models import User,Profile,Measurement,WaterLog,Medicine,Document
from backend.extensions import db
from backend.common import local_day,day_bounds
from backend.services.ocr_service import extract
from .conftest import csrf,register

def data(r,status=200):
    assert r.status_code==status,r.json
    return r.json['data']
def post(c,url,body):return c.post(url,json=body,headers=csrf(c))
def put(c,url,body):return c.put(url,json=body,headers=csrf(c))
def med(c,app):
    with app.app_context():today=str(local_day(1))
    return data(post(c,'/api/medicines',{'name':'Prescribed medicine','dosage':'As prescribed','schedule_times':['08:30','20:30'],'start_date':today}),201)
def image_file():
    b=BytesIO();Image.new('RGB',(200,200),'white').save(b,format='PNG');b.seek(0);return b
class ProviderResponse:
    status_code=200
    ok=True
    def __init__(self,content):self.content=content
    def json(self):return {'choices':[{'message':{'content':self.content},'finish_reason':'stop'}]}
def provider(monkeypatch,result,captured=None):
    def call(*args,**kwargs):
        if captured is not None:captured.append(kwargs['json'])
        return ProviderResponse(json.dumps(result) if isinstance(result,dict) else result)
    monkeypatch.setattr('backend.services.groq_service.requests.post',call)

def test_auth_cookie_password_csrf_logout(logged,app):
    c=logged
    assert c.get_cookie('access_token_cookie').http_only
    assert not c.get_cookie('csrf_access_token').http_only
    assert c.post('/api/water/log',json={'amount_ml':250}).status_code==401
    with app.app_context():assert User.query.first().password_hash!='Password123!'
    token=c.get_cookie('access_token_cookie').value
    data(post(c,'/api/auth/logout',{}))
    c.set_cookie('access_token_cookie',token)
    assert c.get('/api/auth/me').status_code==401

def test_register_login_and_duplicate(client):
    register(client)
    assert client.post('/api/auth/register',json={'name':' TEST Patient ','password':'Password123!','consent':True}).status_code==409
    assert client.post('/api/auth/login',json={'name':'Test Patient','password':'Incorrect123','consent':True}).status_code==401
    data(client.post('/api/auth/login',json={'name':'Test Patient','password':'Password123!','consent':True}))
    assert client.post('/api/auth/register',json={'name':'No Consent','password':'Password123!','consent':False}).status_code==422

@pytest.mark.parametrize('url', ['/api/profile','/api/medicines','/api/health/measurements','/api/documents','/api/assistant/history','/api/maps/config'])
def test_requires_auth(client,url):assert client.get(url).status_code==401

def test_health_profile_dashboard(logged):
    c=logged
    p=data(put(c,'/api/profile',{'age':25,'weight_kg':70,'height_cm':175,'timezone':'Asia/Kolkata'}))
    assert p['bmi']==22.9
    data(post(c,'/api/health/measurements',{'bp_systolic':120,'bp_diastolic':80,'heart_rate':74}),201)
    d=data(c.get('/api/dashboard'));assert d['latest']['heart_rate']==74 and len(d['vitals'])==1
    assert data(c.get('/api/health/measurements'))[0]['bp_diastolic']==80

@pytest.mark.parametrize('payload',[{'bp_systolic':'oops'},{'bp_systolic':400},{'bp_systolic':120,'bp_diastolic':130},{},{'heart_rate':float('nan')},{'user_id':99,'heart_rate':74}])
def test_invalid_readings(logged,payload):assert post(logged,'/api/health/measurements',payload).status_code==422

def test_invalid_profiles_and_bodies(logged):
    assert put(logged,'/api/profile',{'age':200}).status_code==422
    assert put(logged,'/api/profile',{'timezone':'No/SuchZone'}).status_code==422
    assert post(logged,'/api/water/log',[]).status_code==422
    assert post(logged,'/api/water/log',{'amount_ml':0}).status_code==422

def test_medicine_dose_idempotency_edit_delete(logged,app):
    c=logged;m=med(c,app);dose={'scheduled_date':m['start_date'],'scheduled_time':'08:30','status':'taken'}
    data(post(c,f"/api/medicines/{m['id']}/log",dose),201)
    assert post(c,f"/api/medicines/{m['id']}/log",dose).status_code==409
    assert len(data(c.get(f"/api/medicines/{m['id']}/logs")))==1
    assert data(c.get('/api/dashboard'))['adherence_percent']==50
    body={k:v for k,v in m.items() if k!='id'};body['name']='Edited medicine'
    data(put(c,f"/api/medicines/{m['id']}",body))
    body['user_id']=99
    assert put(c,f"/api/medicines/{m['id']}",body).status_code==422
    data(c.delete(f"/api/medicines/{m['id']}",headers=csrf(c)))
    assert data(c.get('/api/medicines'))==[]

def test_medicine_invalid_schedule(logged,app):
    m=med(logged,app);body={k:v for k,v in m.items() if k!='id'}
    body['schedule_times']=['27:00'];assert post(logged,'/api/medicines',body).status_code==422
    body['schedule_times']=['08:30'];body['end_date']='2000-01-01';assert post(logged,'/api/medicines',body).status_code==422

def test_water_timezone_and_delete(logged,app):
    c=logged;row=data(post(c,'/api/water/log',{'amount_ml':250}),201)
    assert data(c.get('/api/water/summary'))['today_total_ml']==250
    with app.app_context():
        start,end=day_bounds(1)
        db.session.add(WaterLog(user_id=1,amount_ml=100,timestamp=start-timedelta(seconds=1)));db.session.commit()
    assert data(c.get('/api/water/summary'))['today_total_ml']==250
    data(c.delete(f"/api/water/logs/{row['id']}",headers=csrf(c)))
    assert data(c.get('/api/water/summary'))['today_total_ml']==0

def test_cross_account_isolation(logged,app):
    first=logged;m=med(first,app)
    data(post(first,'/api/health/measurements',{'heart_rate':75}),201)
    second=app.test_client();register(second,'Second Patient')
    assert data(second.get('/api/health/measurements'))==[]
    assert data(second.get('/api/medicines'))==[]
    assert second.delete(f"/api/medicines/{m['id']}",headers=csrf(second)).status_code==404
    assert second.get(f"/api/medicines/{m['id']}/logs").status_code==404

def test_chat_real_contract_history_context(logged,monkeypatch):
    captured=[];provider(monkeypatch,'A clear educational answer.',captured)
    thread=str(uuid4());c=logged
    data(post(c,'/api/health/measurements',{'heart_rate':77}),201)
    assert 'educational' in data(post(c,'/api/assistant/chat',{'message':'Explain my readings','thread_id':thread}))['reply']
    data(post(c,'/api/assistant/chat',{'message':'What about my last question?','thread_id':thread}))
    assert '77' in captured[0]['messages'][1]['content']
    assert any(m['content']=='Explain my readings' for m in captured[1]['messages'])
    assert len(data(c.get('/api/assistant/history?thread_id='+thread)))==2
    assert len(data(c.get('/api/assistant/threads')))==1

def test_missing_key_is_error(logged,app):
    app.config['GROQ_API_KEY']=''
    r=post(logged,'/api/assistant/chat',{'message':'Hello','thread_id':str(uuid4())})
    assert r.status_code==503
    assert data(logged.get('/api/assistant/history'))==[]

def test_emergency_works_without_provider(logged,app):
    app.config['GROQ_API_KEY']=''
    r=data(post(logged,'/api/symptoms/analyze',{'symptoms':'I cannot breathe'}),201)
    assert r['result']['urgency']=='emergency'

def test_provider_errors_and_schema_rejection(logged,monkeypatch):
    provider(monkeypatch,'not json')
    assert post(logged,'/api/specialists/recommend',{'symptoms':'itchy skin'}).status_code==502
    def fail(*a,**kw):
        r=ProviderResponse('');r.status_code=429;r.ok=False;return r
    monkeypatch.setattr('backend.services.groq_service.requests.post',fail)
    assert post(logged,'/api/assistant/chat',{'message':'Hi','thread_id':str(uuid4())}).status_code==429

def test_report_pipeline_store_download_delete_and_isolation(logged,app,monkeypatch):
    provider(monkeypatch,{'fields':[{'field':'Hemoglobin','value':'13.8','unit':'g/dL','reference_range':None,'status':'unknown'}],'explanation':'The report lists a hemoglobin result.','follow_up':[],'uncertainties':[]})
    c=logged;r=data(c.post('/api/reports/upload',data={'file':(BytesIO(b'Hemoglobin: 13.8 g/dL'),'report.txt')},headers=csrf(c)),201)
    assert r['extracted_text']=='Hemoglobin: 13.8 g/dL' and r['result']['fields'][0]['value']=='13.8'
    assert c.get(f"/api/documents/{r['id']}/file").data==b'Hemoglobin: 13.8 g/dL'
    other=app.test_client();register(other,'Other Patient')
    assert other.get(f"/api/documents/{r['id']}").status_code==404
    assert other.get(f"/api/documents/{r['id']}/file").status_code==404
    assert other.delete(f"/api/documents/{r['id']}",headers=csrf(other)).status_code==404
    data(c.delete(f"/api/documents/{r['id']}",headers=csrf(c)))
    assert not list(app.config['UPLOAD_ROOT'].rglob('*.txt'))

def test_upload_validation_and_failure_cleanup(logged,app):
    c=logged
    assert c.post('/api/prescriptions/scan',data={'file':(BytesIO(b'not a png'),'fake.png')},headers=csrf(c)).status_code==422
    assert c.post('/api/reports/upload',data={'file':(BytesIO(b'<script>'),'evil.html')},headers=csrf(c)).status_code==415
    assert c.post('/api/reports/upload',data={'file':(BytesIO(b'a'* (11*1024*1024)),'huge.txt')},headers=csrf(c)).status_code==413
    app.config['GROQ_API_KEY']=''
    assert c.post('/api/reports/upload',data={'file':(BytesIO(b'Patient report'),'report.txt')},headers=csrf(c)).status_code==503
    assert not list(app.config['UPLOAD_ROOT'].rglob('*.txt'))

def test_real_ocr_and_prescription_structure(logged,app,tmp_path,monkeypatch):
    import shutil
    if not shutil.which('tesseract'):pytest.skip('Tesseract binary not installed')
    im=Image.new('RGB',(1800,450),'white');draw=ImageDraw.Draw(im)
    font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    try:font=ImageFont.truetype(font_path,46)
    except OSError:font=ImageFont.load_default(size=46)
    draw.text((50,80),'TEST DOCUMENT - NOT A PRESCRIPTION\nMedicine Alpha 5 mg - once daily',font=font,fill='black',spacing=25)
    path=tmp_path/'ocr.png';im.save(path)
    with app.app_context():result=extract(path)
    assert 'Medicine Alpha' in result['text']
    provider(monkeypatch,{'medicines':[{'name':'Medicine Alpha','dosage':'5 mg','frequency':'once daily','instructions':None,'duration':None,'source_text':'Medicine Alpha 5 mg - once daily','needs_review':False}],'uncertainties':[],'explanation':'Review all fields.'})
    with path.open('rb') as f:r=data(logged.post('/api/prescriptions/scan',data={'file':(f,'ocr.png')},headers=csrf(logged)),201)
    assert r['result']['medicines'][0]['needs_review'] is True
    assert data(logged.get('/api/medicines'))==[]

def test_xray_sends_actual_pixels_and_keeps_history(logged,monkeypatch):
    calls=[];provider(monkeypatch,{'observations':['Unclear image'],'explanation':'Cannot interpret this image.','limitations':['Not diagnostic'],'next_steps':['Ask a radiologist']},calls)
    r=data(logged.post('/api/xray/analyze',data={'file':(image_file(),'xray.png'),'region':'chest'},headers=csrf(logged)),201)
    assert calls[0]['messages'][-1]['content'][1]['image_url']['url'].startswith('data:image/jpeg;base64,')
    assert r['result']['confidence'] is None
    assert len(data(logged.get('/api/documents?kind=xray')))==1

def test_diet_and_symptoms(logged,monkeypatch):
    assert post(logged,'/api/diet/plan',{}).status_code==422
    data(put(logged,'/api/profile',{'age':26,'height_cm':170,'weight_kg':65}))
    provider(monkeypatch,{'overview':'Balanced meals','meals':['Breakfast','Lunch','Dinner'],'considerations':['Check allergies']})
    assert data(post(logged,'/api/diet/plan',{}),201)['result']['meals'][0]=='Breakfast'
    provider(monkeypatch,{'possible_causes':['Several causes possible'],'urgency':'uncertain','explanation':'More history needed','next_steps':['Contact your clinician'],'specialty':'General medicine'})
    assert data(post(logged,'/api/symptoms/analyze',{'symptoms':'Tired for two days'}),201)['result']['confidence'] is None

def test_maps_key_only_and_static_protection(logged,app):
    assert data(logged.get('/api/maps/config'))=={'api_key':'test-browser-key','provider':'mappls'}
    for url in ['/.env','/backend/config.py','/data/carebot.db','/data/uploads/1/test.png','/api/not-found']:
        assert logged.get(url).status_code==404
    assert b'CareBot' in logged.get('/').data
    app.config['MAPPLS_API_KEY']='';assert logged.get('/api/maps/config').status_code==503

def test_restart_persists_records_and_revocation(logged,app):
    from backend.app import create_app
    data(post(logged,'/api/water/log',{'amount_ml':321}),201)
    token=logged.get_cookie('access_token_cookie').value
    data(post(logged,'/api/auth/logout',{}))
    again=create_app({'TESTING':True,'SQLALCHEMY_DATABASE_URI':app.config['SQLALCHEMY_DATABASE_URI'],'JWT_SECRET_KEY':app.config['JWT_SECRET_KEY'],'UPLOAD_ROOT':app.config['UPLOAD_ROOT'],'RATELIMIT_ENABLED':False})
    client=again.test_client();client.set_cookie('access_token_cookie',token)
    assert client.get('/api/auth/me').status_code==401
    data(client.post('/api/auth/login',json={'name':'Test Patient','password':'Password123!','consent':True}))
    assert data(client.get('/api/water/summary'))['today_total_ml']==321
