"""Run locally: python scripts/create_admin.py (no public admin registration)."""
import sys
from pathlib import Path
from getpass import getpass
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app import create_app
from backend.extensions import db
from backend.models import User,Profile,AdminAccess
from backend.schemas import Auth,ProfileInput
from werkzeug.security import generate_password_hash

def main():
    app=create_app()
    name=' '.join(input('New administrator account name: ').split())
    password=getpass('Password (at least 12 characters): ')
    if len(password)<12: raise SystemExit('Use at least 12 characters.')
    if password!=getpass('Confirm password: '): raise SystemExit('Passwords did not match.')
    Auth(name=name,password=password,consent=True)
    with app.app_context():
        if User.query.filter_by(username=name.casefold()).first():
            raise SystemExit('This name already exists. Choose a separate administrator account name.')
        user=User(name=name,username=name.casefold(),password_hash=generate_password_hash(password))
        db.session.add(user);db.session.flush()
        db.session.add(Profile(user_id=user.id,data=ProfileInput().model_dump()))
        db.session.add(AdminAccess(user_id=user.id));db.session.commit()
    print('Administrator created. Use the Admin sign in link on the login page.')
if __name__=='__main__': main()
