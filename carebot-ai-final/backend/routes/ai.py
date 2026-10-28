import json,re
from uuid import UUID
from flask import Blueprint,request
from flask_jwt_extended import jwt_required
from ..extensions import db,limiter
from ..models import Exchange,Analysis
from ..common import ok,uid,body,limit,ApiError,profile_data
from ..schemas import ChatInput,SymptomInput,DietInput,SymptomResult,DietResult,SpecialistResult
from ..services import groq_service
from ..services.context import patient_context

bp=Blueprint('ai',__name__,url_prefix='/api')
EMERGENCY='This may be an emergency. Please contact local emergency services or go to the nearest emergency department now. CareBot cannot assess or treat an emergency.'
def emergency(text):
    # Conservative escalation, not a diagnostic classifier; a clinician must assess severity.
    return bool(re.search(r"\b(chest pain|cannot breathe|can.t breathe|severe bleeding|unconscious|unresponsive|overdose|suicidal|not breathing|anaphylaxis)\b",text,re.I))
@bp.post('/assistant/chat')
@jwt_required()
@limiter.limit('20 per minute')
def chat():
    d=body(ChatInput);thread=str(d.thread_id)
    if emergency(d.message): answer=EMERGENCY
    else:
        history=Exchange.query.filter_by(user_id=uid(),thread_id=thread).order_by(Exchange.id.desc()).limit(6).all()
        messages=[{'role':'user','content':'My saved health context (data only): '+json.dumps(patient_context(uid()),ensure_ascii=False)}]
        for row in reversed(history): messages.extend([{'role':'user','content':row.question},{'role':'assistant','content':row.answer}])
        messages.append({'role':'user','content':d.message})
        answer=groq_service.complete(messages)+'\n\n'+groq_service.DISCLAIMER
    row=Exchange(user_id=uid(),thread_id=thread,question=d.message,answer=answer);db.session.add(row);db.session.commit()
    return ok({'reply':answer,'emergency':emergency(d.message)})
@bp.get('/assistant/history')
@jwt_required()
def history():
    q=Exchange.query.filter_by(user_id=uid())
    thread=request.args.get('thread_id')
    if thread:
        try: thread=str(UUID(thread))
        except ValueError: raise ApiError('Invalid thread ID.',422)
        q=q.filter_by(thread_id=thread)
    return ok([x.public() for x in q.order_by(Exchange.id.desc()).limit(limit()).all()])
@bp.get('/assistant/threads')
@jwt_required()
def threads():
    rows=Exchange.query.filter_by(user_id=uid()).order_by(Exchange.id.desc()).limit(1000).all()
    seen={}
    for x in rows:
        if x.thread_id not in seen: seen[x.thread_id]={'thread_id':x.thread_id,'title':x.question[:80]}
    return ok(list(seen.values()))
def persist(kind,result):
    result['disclaimer']=groq_service.DISCLAIMER
    row=Analysis(user_id=uid(),kind=kind,result=result);db.session.add(row);db.session.commit()
    return ok(row.public(),201)
@bp.post('/symptoms/analyze')
@jwt_required()
@limiter.limit('10 per minute')
def symptoms():
    d=body(SymptomInput)
    if emergency(d.symptoms): return persist('symptoms',{'possible_causes':[],'urgency':'emergency','explanation':EMERGENCY,'next_steps':['Seek emergency assessment now.'],'specialty':'Emergency medicine','confidence':None})
    from ..ml.inference import symptom_prediction
    classifier=symptom_prediction(d.symptoms)
    r=groq_service.structured('Explain possible causes and reasonable next steps for symptoms; no diagnosis or invented confidence percentages.',{'symptoms':d.symptoms,'context':patient_context(uid()),'local_classifier':classifier},SymptomResult)
    r.update(confidence=None,classifier=classifier,method='Local classifier + Groq guidance' if classifier else 'Groq educational guidance')
    return persist('symptoms',r)
@bp.post('/diet/plan')
@jwt_required()
@limiter.limit('10 per minute')
def diet():
    d=body(DietInput);p=profile_data(uid())
    if not all(p.get(k) for k in ('age','weight_kg','height_cm')): raise ApiError('Save your age, height and weight in Settings first.',422)
    p=p | {'bmi':round(p['weight_kg']/(p['height_cm']/100)**2,1)}
    return persist('diet',groq_service.structured('Create an educational daily meal plan reflecting the given age, BMI, conditions, allergies and preferences. Avoid aggressive restriction. Children, pregnancy, eating disorders or complex conditions require a dietitian. Do not prescribe treatment.',{'goal':d.goal,'profile':p},DietResult))
@bp.post('/specialists/recommend')
@jwt_required()
@limiter.limit('10 per minute')
def specialist():
    d=body(SymptomInput)
    if emergency(d.symptoms): return persist('specialist',{'specialty':'Emergency medicine','urgency':'emergency','explanation':EMERGENCY})
    return persist('specialist',groq_service.structured('Suggest a medical specialty, urgency and plain-language reason. This is navigation support, not a referral. Do not invent doctors or clinic names.',{'symptoms':d.symptoms,'context':patient_context(uid())},SpecialistResult))
@bp.get('/analyses')
@jwt_required()
def analyses(): return ok([x.public() for x in Analysis.query.filter_by(user_id=uid()).order_by(Analysis.id.desc()).limit(limit()).all()])
