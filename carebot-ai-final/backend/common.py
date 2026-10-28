from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity
from pydantic import ValidationError
from .extensions import db
from .models import Profile

class ApiError(Exception):
    def __init__(self, message, status=400):
        self.message, self.status = message, status

def ok(data=None, status=200):
    return jsonify(success=True, data=data), status

def body(schema):
    value = request.get_json(silent=True)
    if not isinstance(value, dict): raise ApiError('A JSON object is required.', 422)
    try: return schema.model_validate(value)
    except ValidationError as e:
        details = '; '.join(f"{'.'.join(map(str,x['loc']))}: {x['msg']}" for x in e.errors())
        raise ApiError(details, 422)

def uid(): return int(get_jwt_identity())

def owned(model, id):
    item = db.session.get(model,id)
    if not item or item.user_id != uid(): raise ApiError('Record not found.',404)
    return item

def profile_data(user_id):
    p = db.session.get(Profile,user_id)
    return p.data if p else {}

def local_day(user_id):
    tz = ZoneInfo(profile_data(user_id).get('timezone','Asia/Kolkata'))
    return datetime.now(tz).date()

def day_bounds(user_id):
    tz = ZoneInfo(profile_data(user_id).get('timezone','Asia/Kolkata'))
    start = datetime.combine(local_day(user_id),time.min,tzinfo=tz)
    return tuple(x.astimezone(timezone.utc).replace(tzinfo=None) for x in (start,start+timedelta(days=1)))

def limit():
    n = request.args.get('limit',50,type=int)
    return max(1,min(n or 50,200))
