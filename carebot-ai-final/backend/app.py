from pathlib import Path
from flask import Flask, send_from_directory, request
from werkzeug.exceptions import HTTPException
from .config import Config, ROOT
from .extensions import db, jwt, limiter
from .common import ApiError, ok
from .models import RevokedToken

def create_app(overrides=None):
    app = Flask(__name__,static_folder=None)
    app.config.from_object(Config)
    app.config.update(overrides or {})
    if len(app.config['JWT_SECRET_KEY']) < 32:
        raise RuntimeError('Set JWT_SECRET in the root .env. Run: python scripts/init_env.py')
    (ROOT/'data').mkdir(exist_ok=True)
    Path(app.config['UPLOAD_ROOT']).mkdir(parents=True,exist_ok=True)
    db.init_app(app); jwt.init_app(app); limiter.init_app(app)
    from .routes import auth, health, medicines, water, documents, ai, maps, admin
    for module in (auth,health,medicines,water,documents,ai,maps,admin): app.register_blueprint(module.bp)
    @jwt.token_in_blocklist_loader
    def revoked(header,payload): return db.session.get(RevokedToken,payload['jti']) is not None
    def auth_error(*args): return {'success':False,'message':'Your session expired or is invalid. Please sign in again.'},401
    jwt.unauthorized_loader(auth_error); jwt.invalid_token_loader(auth_error)
    jwt.expired_token_loader(auth_error); jwt.revoked_token_loader(auth_error)
    @app.errorhandler(ApiError)
    def known_error(e):
        db.session.rollback()
        return {'success':False,'message':e.message},e.status
    @app.errorhandler(HTTPException)
    def http_error(e): return {'success':False,'message':e.description},e.code
    @app.errorhandler(Exception)
    def unexpected(e):
        db.session.rollback()
        # Never log requests, uploaded content, passwords or provider response bodies.
        app.logger.error('Unhandled %s during %s',type(e).__name__,request.path)
        return {'success':False,'message':'Unexpected server error. Please retry.'},500
    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
        if request.path.startswith('/api'): response.headers['Cache-Control']='no-store'
        return response
    @app.get('/api/healthz')
    def healthz(): return ok({'status':'ok','groq_configured':bool(app.config['GROQ_API_KEY'])})
    @app.get('/')
    def index(): return send_from_directory(ROOT/'frontend','index.html')
    @app.get('/<path:path>')
    def static_file(path):
        if not path.startswith(('js/','css/')) and not (path.endswith('.html') and '/' not in path):
            raise ApiError('Not found',404)
        return send_from_directory(ROOT/'frontend',path)
    with app.app_context(): db.create_all()
    return app
