from pathlib import Path
from flask import Blueprint,current_app,send_file,request
from flask_jwt_extended import jwt_required
from ..extensions import db,limiter
from ..models import Document
from ..common import ok,uid,owned,ApiError,limit
from ..schemas import ReportResult,PrescriptionResult,XrayResult
from ..services.uploads import save_upload
from ..services.ocr_service import extract
from ..services import groq_service

bp=Blueprint('documents',__name__,url_prefix='/api')
def upload(kind):
    path,name=save_upload(image_only=kind in ('prescription','xray'))
    try:
        ocr=None
        if kind=='xray':
            region=request.form.get('region','').strip().lower()
            if region not in ('chest','bone'): raise ApiError('Select chest or bone.',422)
            from ..ml.inference import xray_prediction
            classifier=xray_prediction(path,region)
            result=groq_service.structured('Describe only visible educational observations. If this is not a usable X-ray, say so. Do not diagnose pneumonia or fractures, rule out disease, or claim to be a CNN. No confidence percentages.',{'region':region,'local_classifier':classifier},XrayResult,path)
            result.update(provider='Local CNN + Groq vision' if classifier else 'Groq vision',region=region,confidence=classifier['score'] if classifier else None,classifier=classifier,disclaimer=groq_service.DISCLAIMER)
        else:
            ocr=extract(path)
            if kind=='prescription':
                result=groq_service.structured('Structure this prescription OCR text verbatim. Never guess medicine names, strength, dose, frequency or duration. Use null when absent/unclear. Include the exact source text for each medicine. Flag ambiguities. This is transcription, not prescribing.',ocr,PrescriptionResult)
                for m in result['medicines']: m['needs_review']=True
            else:
                result=groq_service.structured('Explain this medical report. Extract all stated test results and retain the original values and units. Reference ranges and flags must appear in the source; otherwise use null and unknown. Explain non-tabular findings too. Identify OCR ambiguities.',ocr,ReportResult)
            result['disclaimer']=groq_service.DISCLAIMER
        d=Document(user_id=uid(),kind=kind,filename=name,storage_name=path.name,extracted_text=ocr['text'] if ocr else '',ocr=ocr,result=result)
        db.session.add(d);db.session.commit()
        return ok(d.public(True),201)
    except Exception:
        db.session.rollback();path.unlink(missing_ok=True);raise
@bp.post('/reports/upload')
@jwt_required()
@limiter.limit('10 per minute')
def reports_upload(): return upload('report')
@bp.post('/prescriptions/scan')
@jwt_required()
@limiter.limit('10 per minute')
def prescription_upload(): return upload('prescription')
@bp.post('/xray/analyze')
@jwt_required()
@limiter.limit('10 per minute')
def xray_upload(): return upload('xray')
@bp.get('/documents')
@jwt_required()
def list_docs():
    query=Document.query.filter_by(user_id=uid())
    kind=request.args.get('kind')
    if kind:
        if kind not in ('report','prescription','xray'): raise ApiError('Unknown document kind.',422)
        query=query.filter_by(kind=kind)
    return ok([d.public() for d in query.order_by(Document.created_at.desc()).limit(limit()).all()])
@bp.get('/documents/<int:id>')
@jwt_required()
def detail(id): return ok(owned(Document,id).public(True))
@bp.get('/documents/<int:id>/file')
@jwt_required()
def original(id):
    d=owned(Document,id)
    return send_file(Path(current_app.config['UPLOAD_ROOT'])/str(uid())/d.storage_name,as_attachment=True,download_name=d.filename)
@bp.delete('/documents/<int:id>')
@jwt_required()
def delete(id):
    d=owned(Document,id);path=Path(current_app.config['UPLOAD_ROOT'])/str(uid())/d.storage_name
    db.session.delete(d);db.session.commit();path.unlink(missing_ok=True);return ok()
