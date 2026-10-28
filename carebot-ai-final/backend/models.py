from datetime import datetime, timezone
from .extensions import db

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

def stamp(value):
    return value.isoformat() + 'Z' if value else None

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    def public(self):
        return {'id': self.id, 'name': self.name, 'username': self.username, 'role': 'admin' if db.session.get(AdminAccess,self.id) else 'patient'}

class RevokedToken(db.Model):
    jti = db.Column(db.String(64), primary_key=True)
    expires_at = db.Column(db.DateTime, nullable=False)

class Profile(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    data = db.Column(db.JSON, nullable=False, default=dict)

class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    bp_systolic = db.Column(db.Integer)
    bp_diastolic = db.Column(db.Integer)
    heart_rate = db.Column(db.Integer)
    weight_kg = db.Column(db.Float)
    height_cm = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    def public(self):
        return {k: getattr(self, k) for k in ['id','bp_systolic','bp_diastolic','heart_rate','weight_kg','height_cm']} | {'timestamp': stamp(self.timestamp)}

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    dosage = db.Column(db.String(120), nullable=False)
    instructions = db.Column(db.String(1000), default='')
    schedule_times = db.Column(db.JSON, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    reminder_enabled = db.Column(db.Boolean, default=True, nullable=False)
    def public(self):
        return {k: getattr(self,k) for k in ['id','name','dosage','instructions','schedule_times','reminder_enabled']} | {'start_date': self.start_date.isoformat(), 'end_date': self.end_date.isoformat() if self.end_date else None}

class Dose(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'), nullable=False, index=True)
    scheduled_date = db.Column(db.Date, nullable=False)
    scheduled_time = db.Column(db.String(5), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, default=utcnow, nullable=False)
    __table_args__ = (db.UniqueConstraint('medicine_id','scheduled_date','scheduled_time'),)
    def public(self):
        return {'id':self.id,'medicine_id':self.medicine_id,'scheduled_date':str(self.scheduled_date),'scheduled_time':self.scheduled_time,'status':self.status,'timestamp':stamp(self.timestamp)}

class WaterLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    amount_ml = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    def public(self):
        return {'id':self.id,'amount_ml':self.amount_ml,'timestamp':stamp(self.timestamp)}

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    kind = db.Column(db.String(20), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    storage_name = db.Column(db.String(64), nullable=False)
    extracted_text = db.Column(db.Text, default='')
    ocr = db.Column(db.JSON)
    result = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    def public(self, detail=False):
        d = {'id':self.id,'kind':self.kind,'filename':self.filename,'created_at':stamp(self.created_at)}
        if detail: d.update(extracted_text=self.extracted_text,ocr=self.ocr,result=self.result)
        return d

class Exchange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    thread_id = db.Column(db.String(36), nullable=False, index=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    def public(self):
        return {'id':self.id,'thread_id':self.thread_id,'user_message':self.question,'assistant_response':self.answer,'timestamp':stamp(self.created_at)}

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    kind = db.Column(db.String(20), nullable=False)
    result = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    def public(self):
        return {'id':self.id,'kind':self.kind,'result':self.result,'created_at':stamp(self.created_at)}

# Separate access table: existing patient databases upgrade without rewriting users.
class AdminAccess(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

class WaterReminder(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    next_due_at = db.Column(db.DateTime, nullable=False)
