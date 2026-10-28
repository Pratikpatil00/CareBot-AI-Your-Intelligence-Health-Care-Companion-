"""StdIO transport for DOM integration tests; uses actual Flask routes, no network."""
import sys,json,tempfile
from pathlib import Path
from backend.app import create_app
from backend.extensions import db

def main():
    with tempfile.TemporaryDirectory() as folder:
        app=create_app({'TESTING':True,'SQLALCHEMY_DATABASE_URI':'sqlite:///'+folder+'/test.db','JWT_SECRET_KEY':'dom-test-secret-at-least-32-characters','UPLOAD_ROOT':Path(folder)/'uploads','RATELIMIT_ENABLED':False,'GROQ_API_KEY':'','MAPPLS_API_KEY':''})
        # Test-only admin fixture; never seeded by the application.
        from backend.models import User,AdminAccess
        from werkzeug.security import generate_password_hash
        with app.app_context():
            admin=User(name='DOM Admin',username='dom admin',password_hash=generate_password_hash('DOMAdminPassword123!'))
            db.session.add(admin);db.session.flush();db.session.add(AdminAccess(user_id=admin.id));db.session.commit()
        client=app.test_client()
        for line in sys.stdin:
            req=json.loads(line)
            r=client.open(req['path'],method=req['method'],json=req.get('body'),headers=req.get('headers',{}))
            cookie=client.get_cookie('csrf_access_token')
            print(json.dumps({'id':req['id'],'status':r.status_code,'json':r.get_json(),'csrf':cookie.value if cookie else None}),flush=True)
        with app.app_context():db.session.remove();db.engine.dispose()
if __name__=='__main__':main()
