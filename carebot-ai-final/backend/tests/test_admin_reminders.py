from datetime import timedelta,date
import sqlite3
from werkzeug.security import generate_password_hash
from backend.app import create_app
from backend.extensions import db
from backend.models import User,AdminAccess,Profile,WaterReminder,Measurement,Medicine,Dose,WaterLog,Document,Exchange,Analysis,utcnow
from .conftest import register,csrf

AUTH={'name':'Test Patient','password':'Password123!','consent':True}

def make_admin(app):
    with app.app_context():
        user=User(name='Owner Admin',username='owner admin',password_hash=generate_password_hash('AdminPassword123!'))
        db.session.add(user);db.session.flush();id=user.id
        db.session.add(AdminAccess(user_id=id));db.session.commit()
    client=app.test_client()
    assert client.post('/api/auth/admin-login',json={'name':'Owner Admin','password':'AdminPassword123!','consent':True}).status_code==200
    return client,id

def test_patient_cannot_use_admin_routes_or_choose_role(logged):
    for path in ['/api/admin/patients','/api/admin/patients/1','/api/admin/patients/1/records/chats','/api/admin/patients/1/documents/1/file']:
        assert logged.get(path).status_code==403
    assert logged.post('/api/auth/admin-login',json=AUTH).status_code==401
    assert logged.post('/api/auth/register',json=AUTH|{'name':'Escalation','role':'admin'}).status_code==422
    assert logged.put('/api/profile',json={'role':'admin'},headers=csrf(logged)).status_code==422
    assert logged.get('/api/auth/me').json['data']['role']=='patient'

def test_anonymous_admin_denied(client):
    assert client.get('/api/admin/patients').status_code==401

def test_admin_records_and_revoked_role(app,logged):
    patient_id=logged.get('/api/auth/me').json['data']['id']
    with app.app_context():
        db.session.add(Measurement(user_id=patient_id,height_cm=170,weight_kg=65))
        medicine=Medicine(user_id=patient_id,name='Prescribed medicine',dosage='As prescribed',schedule_times=['08:00'],start_date=date.today())
        db.session.add(medicine);db.session.flush()
        db.session.add(Dose(medicine_id=medicine.id,scheduled_date=date.today(),scheduled_time='08:00',status='taken'))
        db.session.add(WaterLog(user_id=patient_id,amount_ml=250))
        doc=Document(user_id=patient_id,kind='report',filename='report.txt',storage_name='original.txt',extracted_text='Private report',result={'explanation':'Saved analysis'})
        db.session.add(doc);db.session.flush();doc_id=doc.id
        folder=app.config['UPLOAD_ROOT']/str(patient_id);folder.mkdir(parents=True);(folder/'original.txt').write_text('Private original')
        db.session.add(Exchange(user_id=patient_id,thread_id='test',question='Private question',answer='Saved answer'))
        db.session.add(Analysis(user_id=patient_id,kind='diet',result={'overview':'Saved plan'}));db.session.commit()
    admin,admin_id=make_admin(app)
    listing=admin.get('/api/admin/patients').json['data']
    assert listing['total']==1 and listing['items'][0]['id']==patient_id
    assert 'password_hash' not in str(listing)
    info=admin.get(f'/api/admin/patients/{patient_id}').json['data']
    for kind in info['counts']:
        data=admin.get(f'/api/admin/patients/{patient_id}/records/{kind}').json['data']
        assert data['total']==1 and len(data['items'])==1
        assert 'storage_name' not in str(data)
    assert admin.get(f'/api/admin/patients/{patient_id}/documents/{doc_id}/file').data==b'Private original'
    assert admin.get(f'/api/admin/patients/{admin_id}/documents/{doc_id}/file').status_code==404
    # Existing JWT remains valid, but removing the DB permission takes effect immediately.
    with app.app_context():db.session.delete(db.session.get(AdminAccess,admin_id));db.session.commit()
    assert admin.get('/api/admin/patients').status_code==403

def test_admin_paging_and_literal_search(app,logged):
    with app.app_context():
        for n in range(51):db.session.add(User(name=f'Patient {n}',username=f'p{n}',password_hash='unused'))
        db.session.commit()
    admin,_=make_admin(app)
    a=admin.get('/api/admin/patients').json['data'];b=admin.get('/api/admin/patients?page=2').json['data']
    assert len(a['items'])==50 and a['has_more'] and len(b['items'])==2 and not b['has_more']
    assert admin.get('/api/admin/patients?q=%25').json['data']['total']==0
    assert admin.get('/api/admin/patients?page=bad').status_code==422

def test_login_measurements_only_after_correct_password(app,logged):
    assert logged.post('/api/auth/login',json=AUTH|{'password':'WrongPassword','height_cm':180,'weight_kg':80}).status_code==401
    assert logged.get('/api/profile').json['data']['height_cm'] is None
    assert logged.post('/api/auth/login',json=AUTH|{'height_cm':175,'weight_kg':70}).status_code==200
    p=logged.get('/api/profile').json['data'];assert p['height_cm']==175 and p['weight_kg']==70 and p['bmi']==22.9
    assert len(logged.get('/api/health/measurements').json['data'])==1
    assert logged.post('/api/auth/login',json=AUTH|{'height_cm':None,'weight_kg':None}).status_code==200
    assert logged.get('/api/profile').json['data']['height_cm']==175
    assert logged.post('/api/auth/login',json=AUTH|{'height_cm':-1}).status_code==422
    assert logged.get('/api/profile').json['data']['height_cm']==175

def test_register_measurements(client):
    assert client.post('/api/auth/register',json=AUTH|{'height_cm':160,'weight_kg':60}).status_code==201
    assert client.get('/api/profile').json['data']['height_cm']==160

def settings(client,**values):
    p=client.get('/api/profile').json['data'];p.pop('bmi');p.update(values)
    r=client.put('/api/profile',json=p,headers=csrf(client));assert r.status_code==200

def due_now(app,user_id=1):
    with app.app_context():
        db.session.get(WaterReminder,user_id).next_due_at=utcnow()-timedelta(seconds=1);db.session.commit()

def test_water_enabled_due_snooze_log_pause(app,logged):
    assert not logged.get('/api/water/reminder').json['data']['enabled']
    settings(logged,water_reminder_minutes=1)
    state=logged.get('/api/water/reminder').json['data'];assert state['enabled'] and not state['due']
    due_now(app)
    assert logged.get('/api/water/reminder').json['data']['due']
    assert logged.post('/api/water/reminder/snooze').status_code==401
    state=logged.post('/api/water/reminder/snooze',headers=csrf(logged)).json['data'];assert not state['due']
    with app.app_context():assert db.session.get(WaterReminder,1).next_due_at>utcnow()+timedelta(minutes=9)
    due_now(app)
    assert logged.post('/api/water/log',json={'amount_ml':250},headers=csrf(logged)).status_code==201
    assert not logged.get('/api/water/reminder').json['data']['due']
    settings(logged,water_reminder_minutes=0)
    assert not logged.get('/api/water/reminder').json['data']['enabled']

def test_water_goal_and_other_user_isolation(app,logged):
    settings(logged,water_reminder_minutes=1,water_target_ml=250)
    logged.post('/api/water/log',json={'amount_ml':250},headers=csrf(logged));due_now(app)
    state=logged.get('/api/water/reminder').json['data'];assert state['goal_met'] and not state['due']
    other=app.test_client();register(other,'Other Patient')
    assert not other.get('/api/water/reminder').json['data']['enabled']
    other.post('/api/water/reminder/snooze',headers=csrf(other))
    assert logged.get('/api/water/reminder').json['data']['next_due_at']==state['next_due_at']

def test_upgrade_existing_database_keeps_patients(tmp_path):
    file=tmp_path/'old.db'
    conn=sqlite3.connect(file)
    conn.execute('CREATE TABLE user (id INTEGER PRIMARY KEY,name VARCHAR(120) NOT NULL,username VARCHAR(120) NOT NULL UNIQUE,password_hash VARCHAR(255) NOT NULL,created_at DATETIME NOT NULL)')
    conn.execute("INSERT INTO user VALUES (1,'Existing Patient','existing patient',?,'2025-01-01 00:00:00')",(generate_password_hash('Password123!'),));conn.commit();conn.close()
    app=create_app({'TESTING':True,'JWT_SECRET_KEY':'test-secret-long-enough-for-this-test','SQLALCHEMY_DATABASE_URI':'sqlite:///'+str(file),'UPLOAD_ROOT':tmp_path/'uploads','RATELIMIT_ENABLED':False})
    client=app.test_client();r=client.post('/api/auth/login',json=AUTH|{'name':'Existing Patient'})
    assert r.status_code==200 and r.json['data']['role']=='patient'
    with app.app_context():assert User.query.count()==1;assert AdminAccess.query.count()==0;db.session.remove();db.engine.dispose()

def test_reminder_persists_restart_and_goal_schedule_resets(app,logged):
    settings(logged,water_reminder_minutes=1,water_target_ml=250)
    log=logged.post('/api/water/log',json={'amount_ml':250},headers=csrf(logged)).json['data']
    assert logged.get('/api/water/reminder').json['data']['goal_met']
    logged.delete(f"/api/water/logs/{log['id']}",headers=csrf(logged))
    with app.app_context():assert db.session.get(WaterReminder,1).next_due_at<utcnow()+timedelta(minutes=2)
    due_now(app)
    state=logged.get('/api/water/reminder').json['data'];assert state['due']
    restarted=create_app(dict(app.config));again=restarted.test_client()
    assert again.post('/api/auth/login',json=AUTH).status_code==200
    assert again.get('/api/water/reminder').json['data']['next_due_at']==state['next_due_at']
    assert again.get('/api/water/reminder').json['data']['due']
    with restarted.app_context():db.session.remove();db.engine.dispose()

def test_admin_setup_command(app,monkeypatch):
    from scripts import create_admin
    monkeypatch.setattr(create_admin,'create_app',lambda:app)
    monkeypatch.setattr('builtins.input',lambda prompt:'CLI Admin')
    monkeypatch.setattr(create_admin,'getpass',lambda prompt:'StrongAdminPassword123!')
    create_admin.main()
    client=app.test_client()
    r=client.post('/api/auth/admin-login',json={'name':'CLI Admin','password':'StrongAdminPassword123!','consent':True})
    assert r.status_code==200 and r.json['data']['role']=='admin'
    import pytest
    with pytest.raises(SystemExit,match='already exists'):create_admin.main()
