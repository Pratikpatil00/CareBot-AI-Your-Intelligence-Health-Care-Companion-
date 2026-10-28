import pytest
from backend.app import create_app
from backend.extensions import db

@pytest.fixture
def app(tmp_path):
    app=create_app({'TESTING':True,'SQLALCHEMY_DATABASE_URI':'sqlite:///'+str(tmp_path/'test.db'),'JWT_SECRET_KEY':'test-secret-not-for-use-outside-tests-123456','UPLOAD_ROOT':tmp_path/'uploads','RATELIMIT_ENABLED':False,'GROQ_API_KEY':'test-groq-key','MAPPLS_API_KEY':'test-browser-key'})
    yield app
    with app.app_context(): db.session.remove();db.engine.dispose()
@pytest.fixture
def client(app): return app.test_client()
def csrf(client):
    cookie=client.get_cookie('csrf_access_token')
    return {'X-CSRF-TOKEN':cookie.value} if cookie else {}
def register(client,name='Test Patient'):
    r=client.post('/api/auth/register',json={'name':name,'password':'Password123!','consent':True})
    assert r.status_code==201,r.json
    return r.json['data']
@pytest.fixture
def logged(client): register(client);return client
