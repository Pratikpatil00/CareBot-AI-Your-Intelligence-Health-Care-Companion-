from datetime import timedelta
from flask import Blueprint
from flask_jwt_extended import jwt_required
from ..extensions import db
from ..models import WaterLog
from ..schemas import WaterInput
from ..common import body,ok,uid,owned,profile_data,day_bounds,limit

bp=Blueprint('water',__name__,url_prefix='/api/water')
@bp.post('/log')
@jwt_required()
def add():
    from ..services.reminders import reset
    w=WaterLog(user_id=uid(),**body(WaterInput).model_dump());db.session.add(w)
    reset(uid());db.session.commit();return ok(w.public(),201)
@bp.get('/logs')
@jwt_required()
def logs(): return ok([x.public() for x in WaterLog.query.filter_by(user_id=uid()).order_by(WaterLog.timestamp.desc()).limit(limit()).all()])
@bp.delete('/logs/<int:id>')
@jwt_required()
def delete(id):
    from ..services.reminders import reset
    db.session.delete(owned(WaterLog,id));reset(uid());db.session.commit();return ok()
def summary_data(user_id):
    start,end=day_bounds(user_id)
    total=db.session.query(db.func.coalesce(db.func.sum(WaterLog.amount_ml),0)).filter(WaterLog.user_id==user_id,WaterLog.timestamp>=start,WaterLog.timestamp<end).scalar()
    week=db.session.query(db.func.coalesce(db.func.sum(WaterLog.amount_ml),0)).filter(WaterLog.user_id==user_id,WaterLog.timestamp>=start-timedelta(days=6),WaterLog.timestamp<end).scalar()
    target=profile_data(user_id).get('water_target_ml',2000)
    return {'today_total_ml':total,'daily_target_ml':target,'week_total_ml':week,'week_average_ml':round(week/7),'today_progress_percent':round(min(total/target,1)*100)}
@bp.get('/summary')
@jwt_required()
def summary(): return ok(summary_data(uid()))

@bp.get('/reminder')
@jwt_required()
def reminder_status():
    from ..services.reminders import status
    return ok(status(uid()))
@bp.post('/reminder/snooze')
@jwt_required()
def snooze():
    from ..services.reminders import reset,status
    if profile_data(uid()).get('water_reminder_minutes',0): reset(uid(),10)
    db.session.commit()
    return ok(status(uid()))
