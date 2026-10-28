"""Read-only patient administration. Every request checks current DB permission."""
from pathlib import Path
from flask import Blueprint,request,current_app,send_file
from flask_jwt_extended import verify_jwt_in_request
from ..extensions import db
from ..common import ok,ApiError,uid,profile_data
from ..models import User,AdminAccess,Measurement,Medicine,Dose,WaterLog,Document,Exchange,Analysis,stamp

bp=Blueprint('admin',__name__,url_prefix='/api/admin')
@bp.before_request
def authorize():
    verify_jwt_in_request()
    if not db.session.get(AdminAccess,uid()): raise ApiError('Administrator access required.',403)

def patient(id):
    user=db.session.get(User,id)
    if not user or db.session.get(AdminAccess,id): raise ApiError('Patient not found.',404)
    return user

def paging():
    try: page=int(request.args.get('page',1))
    except ValueError: raise ApiError('Invalid page.',422)
    if page<1: raise ApiError('Invalid page.',422)
    return page

def paginated(query,serialize):
    page=paging();total=query.count()
    return {'items':[serialize(x) for x in query.offset((page-1)*50).limit(50)],'page':page,'total':total,'has_more':page*50<total}

@bp.get('/patients')
def patients():
    query=User.query.filter(~User.id.in_(db.select(AdminAccess.user_id)))
    search=request.args.get('q','').strip()[:120]
    if search: query=query.filter(User.name.contains(search,autoescape=True))
    return ok(paginated(query.order_by(User.id.desc()),lambda u:u.public() | {'created_at':stamp(u.created_at)}))

@bp.get('/patients/<int:id>')
def details(id):
    user=patient(id)
    counts={key:model.query.filter_by(user_id=id).count() for key,model in [('measurements',Measurement),('medicines',Medicine),('water',WaterLog),('documents',Document),('chats',Exchange),('analyses',Analysis)]}
    counts['doses']=Dose.query.join(Medicine).filter(Medicine.user_id==id).count()
    return ok({'user':user.public() | {'created_at':stamp(user.created_at)},'profile':profile_data(id),'counts':counts})

@bp.get('/patients/<int:id>/records/<kind>')
def records(id,kind):
    patient(id)
    models={'measurements':Measurement,'medicines':Medicine,'water':WaterLog,'documents':Document,'chats':Exchange,'analyses':Analysis}
    if kind=='doses': query=Dose.query.join(Medicine).filter(Medicine.user_id==id).order_by(Dose.id.desc())
    elif kind in models:
        model=models[kind];query=model.query.filter_by(user_id=id).order_by(model.id.desc())
    else: raise ApiError('Unknown record type.',404)
    return ok(paginated(query,lambda x:x.public(True) if isinstance(x,Document) else x.public()))

@bp.get('/patients/<int:id>/documents/<int:document_id>/file')
def original(id,document_id):
    patient(id);doc=db.session.get(Document,document_id)
    if not doc or doc.user_id!=id: raise ApiError('Document not found.',404)
    return send_file(Path(current_app.config['UPLOAD_ROOT'])/str(id)/doc.storage_name,as_attachment=True,download_name=doc.filename)
