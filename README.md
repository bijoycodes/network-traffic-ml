# Android Network Traffic ML

A small machine-learning service for classifying Android network traffic into
traffic-risk categories. The project trains a scikit-learn model from a CSV
dataset and exposes predictions through a FastAPI application.

> **Important:** This is a research/demo project. Its output is a model
> prediction based on the supplied training data; it is not a malware scanner,
> a security verdict, or proof that traffic is safe.

## What the project does

The project has two parts:

1. **Training** - `ml/train.py` reads `data/training_dataset.csv`, validates the
   required columns, builds a preprocessing and classification pipeline, and
   saves the trained model to `models/traffic_classifier.joblib`.
2. **Serving** - `app.py` starts a FastAPI application that loads the saved
   model and classifies traffic submitted to `POST /predict`.

The classifier uses these six input features:

- `protocol`
- `port`
- `request_size_bytes`
- `response_size_bytes`
- `connection_frequency`
- `domain_source`

The remaining dataset columns provide device, application, session, address,
timestamp, location, and analysis metadata. They are retained in the dataset
but are not currently passed to the model during training.

## Project structure

```text
.
├── app.py                              # FastAPI application and endpoints
├── data/
│   ├── training_dataset.csv            # Labeled training data
│   └── 06_14_2017-..._ISCX.csv        # Reference network-flow CSV
├── ml/
│   ├── __init__.py
│   └── train.py                        # Model training script
├── models/
│   ├── .gitkeep
│   └── traffic_classifier.joblib       # Generated serialized model
├── requirements.txt                    # Python dependencies
└── README.md
```

The reference PCAP-derived CSV is included as data context. The current
training script does not read it directly; training uses
`data/training_dataset.csv`.

## Requirements

- Python 3.10 or newer
- `pip`
- A virtual environment is recommended

The project dependencies are pinned or declared in
[`requirements.txt`](requirements.txt):

- FastAPI
- Uvicorn
- pandas
- scikit-learn
- joblib

## Installation

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

If a `.venv` directory already exists, activate it and install the
requirements:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Train the model

Run training from the repository root:

```bash
source .venv/bin/activate
python -m ml.train
```

The script:

1. Checks that `data/training_dataset.csv` exists.
2. Checks for the required feature and target columns.
3. Converts numeric values and imputes missing feature values.
4. One-hot encodes the categorical features.
5. Trains a `RandomForestClassifier` with 100 trees and balanced class
   weights.
6. Saves the pipeline to:

   ```text
   models/traffic_classifier.joblib
   ```

The script prints the number of rows, label counts, and training-set fit
accuracy. That accuracy is measured on the same rows used for fitting and is
**not** a held-out test score or evidence of real-world performance.

### Training data requirements

The CSV must include these columns:

```text
protocol
port
request_size_bytes
response_size_bytes
connection_frequency
domain_source
risk_level
```

The current dataset also contains these additional metadata columns:

```text
id
device_id
device_name
session_id
app_name
domain
ip
dns
timestamp
total_bytes
geo_location
analysis_result
```

`risk_level` is the prediction target. The current dataset includes these
labels:

- `normal` - routine traffic with no risk indicator in the supplied labels
- `benign` - expected application traffic
- `privacyInvasive` - traffic associated with frequent telemetry or tracking
- `suspicious` - traffic that warrants additional review
- `malicious` - traffic labeled as harmful or strongly deceptive

These meanings describe the labels in this dataset. They should not be
interpreted as independently verified security classifications.

## Run the API

After training, start the development server:

```bash
source .venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

The API is available at:

```text
http://127.0.0.1:8001
```

The `--reload` option is intended for local development. Do not use it as a
production process manager.

## API endpoints

### `GET /`

Returns a basic service status:

```json
{
  "status": "running",
  "message": "Android Network Traffic API is working",
  "version": "1.0.0"
}
```

### `GET /health`

Returns service health and whether the serialized model file exists:

```json
{
  "status": "healthy",
  "ml_connected": true
}
```

`ml_connected` indicates file availability, not model quality or prediction
accuracy.

### `POST /predict`

Submit one traffic record as JSON:

```bash
curl -X POST http://127.0.0.1:8001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "protocol": "HTTPS",
    "port": 443,
    "request_size_bytes": 850,
    "response_size_bytes": 14200,
    "connection_frequency": 42,
    "domain_source": "observed"
  }'
```

Successful responses have this shape:

```json
{
  "status": "success",
  "predicted_risk_level": "normal",
  "ml_connected": true
}
```

The exact predicted label depends on the trained model and input values.

#### Request fields

| Field | Type | Constraints |
|---|---|---|
| `protocol` | string | Required; examples include `HTTPS`, `HTTP`, and `TCP/TLS` |
| `port` | integer or `null` | Optional; if present, must be between 1 and 65535 |
| `request_size_bytes` | integer | Required; must be 0 or greater |
| `response_size_bytes` | integer | Required; must be 0 or greater |
| `connection_frequency` | integer | Required; must be 0 or greater |
| `domain_source` | string | Required; examples include `observed` and `inferred` |

Interactive API documentation is generated by FastAPI:

- Swagger UI: `http://127.0.0.1:8001/docs`
- ReDoc: `http://127.0.0.1:8001/redoc`

## Error behavior

- If the request body does not satisfy the input schema, FastAPI returns a
  validation error, normally with HTTP status `422`.
- If `models/traffic_classifier.joblib` is missing, `POST /predict` returns
  HTTP status `503` and instructs you to run `python -m ml.train`.
- Unknown categorical values are accepted by the preprocessing pipeline because
  the encoder is configured with `handle_unknown="ignore"`.

## Dataset notes

`data/training_dataset.csv` is a labeled, row-oriented traffic dataset. Each
row represents a network event or flow with application and device metadata.
The byte fields are represented in bytes, ports are numeric, and timestamps
are stored as ISO-like UTC strings.

The model currently ignores:

- application name
- domain and IP address
- DNS resolver
- timestamp
- device and session identifiers
- geographic location
- `total_bytes`
- free-text `analysis_result`

Consequently, changing those fields alone does not change a prediction in the
current implementation. To use them, update the feature selection and
preprocessing logic in `ml/train.py`, then retrain the model.

## Development workflow

A typical local workflow is:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m ml.train
uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

In another terminal, check the service:

```bash
curl http://127.0.0.1:8001/health
```

Then open `http://127.0.0.1:8001/docs` to try the prediction endpoint.

## Limitations and responsible use

- The training script does not split data into training and test sets.
- The reported fit accuracy can be optimistic because it is calculated on the
  training rows.
- No probability, confidence, explanation, or feature importance is returned
  by the API.
- The model is only as reliable as the labels and distributions in the
  supplied CSV.
- Network traffic patterns can change over time, so retraining may be needed
  when the data distribution changes.
- Do not use the prediction as the sole basis for blocking traffic, identifying
  malware, or making security decisions.
- Avoid placing secrets, personal data, or sensitive packet contents in the
  dataset or API logs.

## License

No license is currently declared in this repository. Add an explicit
`LICENSE` file before distributing the project or accepting external
contributions.
