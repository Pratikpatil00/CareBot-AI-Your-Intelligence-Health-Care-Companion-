from ..models import Document,Measurement,Medicine
from ..common import profile_data

def patient_context(user_id):
    reports=Document.query.filter_by(user_id=user_id).order_by(Document.created_at.desc()).limit(3).all()
    return {'profile':profile_data(user_id),'latest_measurements':[m.public() for m in Measurement.query.filter_by(user_id=user_id).order_by(Measurement.timestamp.desc()).limit(14).all()],
            'medicines':[m.public() for m in Medicine.query.filter_by(user_id=user_id).limit(40).all()],
            'recent_documents':[{'kind':d.kind,'filename':d.filename,'result':d.result} for d in reports]}
