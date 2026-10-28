# Optional supervised models

No datasets or trained weights were supplied with the project. A working training pipeline is different from a trained, validated medical model. This package includes both training and inference code; it does not invent weights, classes, evaluation results or clinical accuracy. The normal app works through Groq without these dependencies.

## Install dependencies

From the root, using Python 3.11/3.12:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ml.txt
```

Training may be slow on a CPU. TensorFlow is not required for default Groq vision mode. Training/inference code is included but was not executed against a real medical dataset during this build.

## X-ray CNN

Obtain a permitted, de-identified labeled dataset yourself. Split **by patient**, avoiding duplicates or related images across splits. Create:

```text
data/chest/
  train/<actual_class_name>/*.png
  val/<actual_class_name>/*.png
  test/<actual_class_name>/*.png
```

Use the real labels from your dataset; do not rename labels just to claim a supported diagnosis. All three splits must contain the same class directories. The script checks exact duplicate image bytes across splits, but cannot detect that different images belong to the same person: patient-level separation is your responsibility.

```powershell
.\.venv\Scripts\python.exe -m backend.ml.train_xray --dataset data/chest --region chest --epochs 15
```

For bone images, use a separate dataset and `--region bone`.

The script trains a three-convolution CNN, uses the validation split for early stopping, evaluates the untouched test split, and writes actual measured metrics plus:

- `data/models/chest.keras` and `chest.json`, or
- `data/models/bone.keras` and `bone.json`.

Input normalization is inside the saved graph, used identically in training/inference. Classes and image dimensions are read from the generated metadata. Restart CareBot after training. The X-ray route now runs the local CNN and includes its result in the Groq vision/explanation request. The UI shows its class and **uncalibrated softmax score**, separately from the explanation. A high score is not proof of a disease or a clinically calibrated probability. Models accept the selected region but do not contain a validated out-of-distribution detector; inappropriate images can produce meaningless scores.

Do not install arbitrary `.keras` or `joblib` files downloaded from strangers. Use your own trusted training artifacts. No model-upload endpoint exists.

## Symptom classifier

Prepare separate patient-independent UTF-8 CSV files with columns `symptoms,disease`, with real labeled examples. The training set must have at least two classes and five examples per class; much larger, representative data are needed for useful results.

```powershell
.\.venv\Scripts\python.exe -m backend.ml.train_symptoms --train data/symptoms_train.csv --test data/symptoms_test.csv
```

This trains TF-IDF + logistic regression with cross-validated calibration and writes `data/models/symptoms.joblib` and `symptoms.json`. The held-out test report is saved; it is not a claimed real-world clinical accuracy. Restart CareBot. Symptom Checker includes the model's top three estimates alongside Groq guidance. Emergency escalation runs before either model/provider.

The classifier only recognizes its dataset labels. Novel/atypical symptoms, different languages, changed disease prevalence and missing context can make its outputs unreliable. Its estimates must not be presented as a patient's medical probability. Independent evaluation and appropriate clinical review are still required.
