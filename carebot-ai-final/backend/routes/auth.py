from datetime import datetime,timezone
from flask import Blueprint
from flask_jwt_extended import jwt_required,create_access_token,set_access_cookies,unset_jwt_cookies,get_jwt
from werkzeug.security import generate_password_hash,check_password_hash
from sqlalchemy.exc import IntegrityError
from ..extensions import db,limiter
from ..models import User,Profile,RevokedToken,AdminAccess,Measurement
from ..common import body,ok,ApiError,uid
from ..schemas import Auth,ProfileInput

bp=Blueprint('auth',__name__,url_prefix='/api/auth')
def session_response(user,status=200):
    response,code=ok(user.public(),status)
    set_access_cookies(response,create_access_token(identity=str(user.id)))
    return response,code
@bp.post('/register')
@limiter.limit('10 per hour')
def register():
    data=body(Auth)
    name=' '.join(data.name.split())
    if User.query.filter_by(username=name.casefold()).first(): raise ApiError('That full name is already registered. Sign in or use a distinct account name.',409)
    user=User(name=name,username=name.casefold(),password_hash=generate_password_hash(data.password))
    db.session.add(user)
    try: db.session.flush()
    except IntegrityError: raise ApiError('That account already exists.',409)
    db.session.add(Profile(user_id=user.id,data=ProfileInput(height_cm=data.height_cm,weight_kg=data.weight_kg).model_dump()))
    db.session.commit()
    return session_response(user,201)
@bp.post('/login')
@limiter.limit('10 per minute')
def login():
    data=body(Auth)
    user=User.query.filter_by(username=' '.join(data.name.split()).casefold()).first()
    if not user or not check_password_hash(user.password_hash,data.password): raise ApiError('Incorrect account name or password.',401)
    save_login_measurements(user,data)
    return session_response(user)

def save_login_measurements(user,data):
    values={k:getattr(data,k) for k in ('height_cm','weight_kg') if getattr(data,k) is not None}
    if values:
        p=db.session.get(Profile,user.id) or Profile(user_id=user.id,data=ProfileInput().model_dump())
        p.data=p.data | values
        db.session.add(p)
        db.session.add(Measurement(user_id=user.id,**values))
        db.session.commit()

@bp.post('/admin-login')
@limiter.limit('10 per minute')
def admin_login():
    data=body(Auth)
    user=User.query.filter_by(username=' '.join(data.name.split()).casefold()).first()
    if not user or not check_password_hash(user.password_hash,data.password) or not db.session.get(AdminAccess,user.id):
        raise ApiError('Incorrect administrator account or password.',401)
    return session_response(user)

@bp.get('/me')
@jwt_required()
def me():
    user=db.session.get(User,uid())
    if not user: raise ApiError('Account not found.',401)
    return ok(user.public())
@bp.post('/logout')
@jwt_required()
def logout():
    token=get_jwt()
    db.session.add(RevokedToken(jti=token['jti'],expires_at=datetime.fromtimestamp(token['exp'],timezone.utc).replace(tzinfo=None)))
    RevokedToken.query.filter(RevokedToken.expires_at < datetime.now(timezone.utc).replace(tzinfo=None)).delete()
    db.session.commit()
    response,status=ok()
    unset_jwt_cookies(response)
    return response,status
