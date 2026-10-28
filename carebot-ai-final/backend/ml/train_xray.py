"""Train and evaluate a real CNN from user-provided, independently split images.
python -m backend.ml.train_xray --dataset data/chest --region chest --epochs 15
Requires optional requirements-ml.txt. Does not download or fabricate datasets.
"""
import argparse,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from ..config import ROOT

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--region',choices=['chest','bone'],required=True)
    parser.add_argument('--epochs',type=int,default=15)
    args=parser.parse_args()
    paths=[args.dataset/x for x in ('train','val','test')]
    if not all(p.is_dir() for p in paths):parser.error('Dataset needs train/, val/, test/ with class subdirectories. Split by patient before training.')
    classes=sorted(p.name for p in paths[0].iterdir() if p.is_dir())
    if len(classes)<2:parser.error('At least two real labeled classes are required.')
    hashes=[];counts={}
    for p in paths:
        if sorted(x.name for x in p.iterdir() if x.is_dir())!=classes:parser.error('All splits need the same class names.')
        h=set();counts[p.name]={}
        for c in classes:
            files=[x for x in (p/c).rglob('*') if x.suffix.lower() in ('.jpg','.jpeg','.png')]
            if not files:parser.error(f'No images in {p/c}')
            counts[p.name][c]=len(files)
            for f in files:h.add(hashlib.sha256(f.read_bytes()).hexdigest())
        hashes.append(h)
    if any(hashes[i]&hashes[j] for i in range(3) for j in range(i+1,3)):parser.error('Identical image bytes occur across splits; remove data leakage first.')
    import tensorflow as tf
    tf.keras.utils.set_random_seed(42)
    datasets=[tf.keras.utils.image_dataset_from_directory(p,class_names=classes,image_size=(224,224),batch_size=16,label_mode='int',shuffle=(i==0),seed=42) for i,p in enumerate(paths)]
    # Normalization is INSIDE the saved graph, so inference preprocessing agrees.
    model=tf.keras.Sequential([
        tf.keras.layers.Input((224,224,3)),tf.keras.layers.Rescaling(1./255),
        tf.keras.layers.Conv2D(32,3,activation='relu'),tf.keras.layers.MaxPooling2D(),
        tf.keras.layers.Conv2D(64,3,activation='relu'),tf.keras.layers.MaxPooling2D(),
        tf.keras.layers.Conv2D(128,3,activation='relu'),tf.keras.layers.GlobalAveragePooling2D(),
        tf.keras.layers.Dropout(.3),tf.keras.layers.Dense(len(classes),activation='softmax')])
    model.compile(optimizer='adam',loss='sparse_categorical_crossentropy',metrics=['accuracy'])
    model.fit(datasets[0],validation_data=datasets[1],epochs=args.epochs,callbacks=[tf.keras.callbacks.EarlyStopping(patience=3,restore_best_weights=True)])
    metrics=model.evaluate(datasets[2],return_dict=True)
    output=ROOT/'data/models';output.mkdir(parents=True,exist_ok=True)
    model.save(output/f'{args.region}.keras')
    metadata={'region':args.region,'classes':classes,'image_size':[224,224],'counts':counts,'test_metrics':metrics,'trained_at':datetime.now(timezone.utc).isoformat(),'score_type':'uncalibrated softmax class score, not clinical probability','clinical_validation':False}
    (output/f'{args.region}.json').write_text(json.dumps(metadata,indent=2))
    print(json.dumps(metadata,indent=2))
if __name__=='__main__':main()
