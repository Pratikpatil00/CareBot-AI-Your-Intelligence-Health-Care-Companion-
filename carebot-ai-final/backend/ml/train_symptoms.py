"""Train a symptom text classifier using separate labeled CSV train/test files.
Required columns: symptoms, disease. Supply licensed, de-identified real data.
"""
import argparse,csv,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from ..config import ROOT

def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    if not rows or any(not r.get('symptoms') or not r.get('disease') for r in rows):raise ValueError('CSV needs nonempty symptoms and disease columns.')
    return [r['symptoms'].strip() for r in rows],[r['disease'].strip() for r in rows]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--train',type=Path,required=True);p.add_argument('--test',type=Path,required=True);a=p.parse_args()
    x,y=read(a.train);xt,yt=read(a.test)
    if set(v.casefold() for v in x)&set(v.casefold() for v in xt):p.error('Duplicate symptom descriptions across train/test; remove data leakage.')
    if len(set(y))<2 or any(y.count(c)<5 for c in set(y)):p.error('Each of at least two classes needs >=5 training examples.')
    if set(yt)-set(y):p.error('Test set contains labels not represented in training.')
    from sklearn.pipeline import make_pipeline
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.metrics import classification_report
    import joblib
    model=CalibratedClassifierCV(make_pipeline(TfidfVectorizer(ngram_range=(1,2),max_features=20000),LogisticRegression(max_iter=1500,class_weight='balanced')),cv=3)
    model.fit(x,y)
    report=classification_report(yt,model.predict(xt),output_dict=True,zero_division=0)
    output=ROOT/'data/models';output.mkdir(parents=True,exist_ok=True)
    joblib.dump(model,output/'symptoms.joblib')
    metadata={'classes':model.classes_.tolist(),'train_rows':len(x),'test_rows':len(xt),'test_metrics':report,'trained_at':datetime.now(timezone.utc).isoformat(),'clinical_validation':False,'note':'Probabilities are dataset/model estimates, not clinical probabilities.'}
    (output/'symptoms.json').write_text(json.dumps(metadata,indent=2));print(json.dumps(metadata,indent=2))
if __name__=='__main__':main()
