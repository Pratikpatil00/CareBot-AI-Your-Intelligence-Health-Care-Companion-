from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Blueprint
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import Medicine,Dose
from ..schemas import MedicineInput,DoseInput
from ..common import body,ok,uid,owned,local_day,profile_data,ApiError

bp=Blueprint('medicines',__name__,url_prefix='/api/medicines')
@bp.get('')
@jwt_required()
def list_medicines(): return ok([m.public() for m in Medicine.query.filter_by(user_id=uid()).all()])
@bp.post('')
@jwt_required()
def add():
    m=Medicine(user_id=uid(),**body(MedicineInput).model_dump());db.session.add(m);db.session.commit();return ok(m.public(),201)
@bp.put('/<int:id>')
@jwt_required()
def edit(id):
    m=owned(Medicine,id)
    for k,v in body(MedicineInput).model_dump().items(): setattr(m,k,v)
    db.session.commit();return ok(m.public())
@bp.delete('/<int:id>')
@jwt_required()
def delete(id):
    m=owned(Medicine,id);Dose.query.filter_by(medicine_id=id).delete();db.session.delete(m);db.session.commit();return ok()
def schedule_data(user_id):
    today=local_day(user_id)
    now=datetime.now(ZoneInfo(profile_data(user_id).get('timezone','Asia/Kolkata'))).strftime('%H:%M')
    meds=Medicine.query.filter_by(user_id=user_id).all()
    rows=[]
    for m in meds:
        if m.start_date>today or (m.end_date and m.end_date<today): continue
        for t in m.schedule_times:
            dose=Dose.query.filter_by(medicine_id=m.id,scheduled_date=today,scheduled_time=t).first()
            rows.append({'medicine_id':m.id,'name':m.name,'dosage':m.dosage,'scheduled_date':str(today),'scheduled_time':t,'status':dose.status if dose else ('due' if t<=now else 'upcoming'),'reminder_enabled':m.reminder_enabled})
    return sorted(rows,key=lambda x:x['scheduled_time'])
@bp.get('/schedule')
@jwt_required()
def schedule(): return ok(schedule_data(uid()))
@bp.post('/<int:id>/log')
@jwt_required()
def log(id):
    m=owned(Medicine,id);d=body(DoseInput)
    if d.scheduled_time not in m.schedule_times: raise ApiError('That time is not in this medicine schedule.',422)
    if d.scheduled_date>local_day(uid()) or d.scheduled_date<m.start_date or (m.end_date and d.scheduled_date>m.end_date): raise ApiError('Dose date is outside the active schedule or in the future.',422)
    if Dose.query.filter_by(medicine_id=id,scheduled_date=d.scheduled_date,scheduled_time=d.scheduled_time).first(): raise ApiError('That scheduled dose has already been logged.',409)
    row=Dose(medicine_id=id,**d.model_dump());db.session.add(row)
    try: db.session.commit()
    except IntegrityError: raise ApiError('That scheduled dose has already been logged.',409)
    return ok(row.public(),201)
@bp.get('/<int:id>/logs')
@jwt_required()
def logs(id):
    owned(Medicine,id)
    return ok([x.public() for x in Dose.query.filter_by(medicine_id=id).order_by(Dose.timestamp.desc()).limit(200).all()])
