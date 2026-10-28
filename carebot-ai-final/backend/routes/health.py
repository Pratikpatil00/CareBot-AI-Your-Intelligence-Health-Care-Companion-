from datetime import timedelta
from flask import Blueprint
from flask_jwt_extended import jwt_required
from ..extensions import db
from ..models import Profile,Measurement,Document,Exchange
from ..schemas import ProfileInput,MeasurementInput
from ..common import body,ok,uid,profile_data,limit,owned,day_bounds

bp=Blueprint('health',__name__,url_prefix='/api')
@bp.get('/profile')
@jwt_required()
def profile():
    p=profile_data(uid()).copy()
    p['bmi']=round(p['weight_kg']/(p['height_cm']/100)**2,1) if p.get('weight_kg') and p.get('height_cm') else None
    return ok(p)
@bp.put('/profile')
@jwt_required()
def save_profile():
    data=body(ProfileInput).model_dump()
    p=db.session.get(Profile,uid()) or Profile(user_id=uid())
    previous=p.data or {}
    p.data=data;db.session.add(p)
    if any(previous.get(key)!=data[key] for key in ('water_reminder_minutes','water_target_ml','timezone')):
        from ..services.reminders import reset
        reset(uid(),data['water_reminder_minutes'])
    db.session.commit()
    return profile()
@bp.get('/health/measurements')
@jwt_required()
def measurements():
    return ok([m.public() for m in Measurement.query.filter_by(user_id=uid()).order_by(Measurement.timestamp.desc()).limit(limit()).all()])
@bp.post('/health/measurements')
@jwt_required()
def save_measurement():
    data=body(MeasurementInput).model_dump()
    m=Measurement(user_id=uid(),**data);db.session.add(m)
    p=db.session.get(Profile,uid())
    if p:
        p.data=p.data | {k:v for k,v in data.items() if k in ('weight_kg','height_cm') and v is not None}
    db.session.commit()
    return ok(m.public(),201)
@bp.delete('/health/measurements/<int:id>')
@jwt_required()
def delete_measurement(id):
    db.session.delete(owned(Measurement,id));db.session.commit();return ok()
@bp.get('/dashboard')
@jwt_required()
def dashboard():
    from .water import summary_data
    from .medicines import schedule_data
    start,end=day_bounds(uid())
    rows=Measurement.query.filter(Measurement.user_id==uid(),Measurement.timestamp>=start-timedelta(days=6),Measurement.timestamp<end).order_by(Measurement.timestamp).all()
    recent=Measurement.query.filter_by(user_id=uid()).order_by(Measurement.timestamp.desc()).limit(200).all()
    latest={k:next((getattr(m,k) for m in recent if getattr(m,k) is not None),None) for k in ('bp_systolic','bp_diastolic','heart_rate')}
    p=profile_data(uid())
    bmi=round(p['weight_kg']/(p['height_cm']/100)**2,1) if p.get('weight_kg') and p.get('height_cm') else None
    doses=schedule_data(uid())
    taken=sum(x['status']=='taken' for x in doses)
    return ok({'bmi':bmi,'latest':latest,'vitals':[m.public() for m in rows],'water':summary_data(uid()),'schedule':doses,'adherence_percent':round(taken/len(doses)*100) if doses else None,'sources':{'reports':Document.query.filter_by(user_id=uid(),kind='report').count(),'xray':Document.query.filter_by(user_id=uid(),kind='xray').count(),'vitals':Measurement.query.filter_by(user_id=uid()).count()}})
