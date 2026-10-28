from flask import Blueprint,current_app
from flask_jwt_extended import jwt_required
from ..common import ok,ApiError
bp=Blueprint('maps',__name__,url_prefix='/api/maps')
@bp.get('/config')
@jwt_required()
def config():
    key=current_app.config['MAPPLS_API_KEY']
    if not key: raise ApiError('Add MAPPLS_API_KEY to the root .env and restart to enable MapmyIndia / Mappls.',503)
    # Only a domain-restricted public Web SDK static key belongs here.
    return ok({'api_key':key,'provider':'mappls'})
