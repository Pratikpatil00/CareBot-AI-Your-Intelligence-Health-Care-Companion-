from pathlib import Path
from uuid import uuid4
from flask import request,current_app
from werkzeug.utils import secure_filename
from PIL import Image
from ..common import ApiError,uid

def save_upload(image_only=False):
    file=request.files.get('file')
    if not file or not file.filename: raise ApiError('Choose a file to upload.',422)
    name=secure_filename(file.filename)[:220]
    ext=Path(name).suffix.lower()
    allowed={'.png','.jpg','.jpeg','.webp'}
    if not image_only: allowed|={'.pdf','.docx','.txt','.csv'}
    if ext not in allowed: raise ApiError('Unsupported file type. Allowed: '+', '.join(sorted(allowed)),415)
    folder=Path(current_app.config['UPLOAD_ROOT'])/str(uid());folder.mkdir(parents=True,exist_ok=True)
    path=folder/(uuid4().hex+ext)
    file.save(path)
    try:
        if path.stat().st_size==0: raise ApiError('The file is empty.',422)
        if ext in {'.png','.jpg','.jpeg','.webp'}:
            with Image.open(path) as im:
                if im.width*im.height>20_000_000: raise ApiError('Image exceeds 20 megapixels.',422)
                im.verify()
        elif ext=='.pdf' and not path.read_bytes().startswith(b'%PDF-'):
            raise ApiError('File content is not a PDF.',422)
    except Exception as e:
        path.unlink(missing_ok=True)
        if isinstance(e,ApiError): raise
        raise ApiError('Invalid or corrupted image.',422)
    return path,name
