from datetime import timedelta
from ..extensions import db
from ..models import WaterReminder,WaterLog,utcnow,stamp
from ..common import profile_data,day_bounds

def reset(user_id,minutes=None):
    interval=profile_data(user_id).get('water_reminder_minutes',0) if minutes is None else minutes
    row=db.session.get(WaterReminder,user_id)
    if not interval:
        if row: db.session.delete(row)
        return
    if not row: row=WaterReminder(user_id=user_id);db.session.add(row)
    row.next_due_at=utcnow()+timedelta(minutes=interval)

def status(user_id):
    from ..routes.water import summary_data
    p=profile_data(user_id);minutes=p.get('water_reminder_minutes',0)
    if not minutes: return {'enabled':False,'due':False,'next_due_at':None,'interval_minutes':0}
    now=utcnow();row=db.session.get(WaterReminder,user_id)
    if not row:
        last=WaterLog.query.filter_by(user_id=user_id).order_by(WaterLog.timestamp.desc()).first()
        row=WaterReminder(user_id=user_id,next_due_at=(last.timestamp if last else now)+timedelta(minutes=minutes))
        db.session.add(row);db.session.commit()
    summary=summary_data(user_id);goal_met=summary['today_total_ml']>=summary['daily_target_ml']
    # A completed target pauses reminders until the next local day.
    if goal_met:
        _,end=day_bounds(user_id)
        if row.next_due_at<end:
            row.next_due_at=end+timedelta(minutes=minutes);db.session.commit()
    return {'enabled':True,'due':not goal_met and now>=row.next_due_at,'next_due_at':stamp(row.next_due_at),'interval_minutes':minutes,'goal_met':goal_met}
