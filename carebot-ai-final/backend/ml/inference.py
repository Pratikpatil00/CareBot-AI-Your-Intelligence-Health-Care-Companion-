import json
from functools import lru_cache
from pathlib import Path
from PIL import Image,ImageOps
from ..config import ROOT
from ..common import ApiError

MODEL_DIR=ROOT/'data/models'
@lru_cache(maxsize=2)
def load_cnn(path,mtime):
    import tensorflow as tf
    return tf.keras.models.load_model(path,compile=False)
def xray_prediction(path,region):
    model_path=MODEL_DIR/f'{region}.keras';metadata_path=MODEL_DIR/f'{region}.json'
    if not model_path.exists() or not metadata_path.exists():return None
    try:
        import numpy as np
        meta=json.loads(metadata_path.read_text())
        model=load_cnn(str(model_path),model_path.stat().st_mtime)
        with Image.open(path) as im:arr=np.asarray(ImageOps.exif_transpose(im).convert('RGB').resize(tuple(meta['image_size'])),dtype=np.float32)
        probs=model.predict(np.expand_dims(arr,0),verbose=0)[0]
        if len(probs)!=len(meta['classes']) or not np.isfinite(probs).all():raise ValueError('Invalid model shape/output')
        i=int(np.argmax(probs))
        return {'predicted_class':meta['classes'][i],'score':float(probs[i]),'score_type':meta['score_type'],'test_metrics':meta['test_metrics'],'clinical_validation':False}
    except ImportError:raise ApiError('A CNN model is present, but optional ML dependencies are missing. Install requirements-ml.txt.',503)
    except Exception:raise ApiError('The local CNN model could not be loaded. Check its matching metadata and retrain if needed.',503)
@lru_cache(maxsize=1)
def load_symptoms(path,mtime):
    import joblib
    # Only trusted, locally trained artifacts: pickle/joblib can execute code.
    return joblib.load(path)
def symptom_prediction(text):
    path=MODEL_DIR/'symptoms.joblib'
    if not path.exists():return None
    try:
        model=load_symptoms(str(path),path.stat().st_mtime);probs=model.predict_proba([text])[0]
        return {'candidates':sorted([{'condition':str(c),'score':float(s)} for c,s in zip(model.classes_,probs)],key=lambda x:-x['score'])[:3],'score_type':'Model estimate for its dataset labels, not a clinical probability','clinical_validation':False}
    except ImportError:raise ApiError('Install requirements-ml.txt to use the local symptom classifier.',503)
    except Exception:raise ApiError('Local symptom classifier could not be loaded.',503)
