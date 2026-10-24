from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "traffic_classifier.joblib"

app = FastAPI(
    title="Android Network Traffic ML API",
    description="Network traffic classification research API",
    version="1.0.0",
)


class TrafficData(BaseModel):
    protocol: str
    port: int | None = Field(default=None, ge=1, le=65535)
    request_size_bytes: int = Field(ge=0)
    response_size_bytes: int = Field(ge=0)
    connection_frequency: int = Field(ge=0)
    domain_source: str


def load_model():
    if not MODEL_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail=(
                "The trained model is not available. "
                "Run python -m ml.train first."
            ),
        )

    return joblib.load(MODEL_PATH)


@app.get("/")
def home():
    return {
        "status": "running",
        "message": "Android Network Traffic API is working",
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "ml_connected": MODEL_PATH.exists(),
    }


@app.post("/predict")
def predict(data: TrafficData):
    model = load_model()

    features = pd.DataFrame(
        [
            {
                "protocol": data.protocol,
                "port": data.port,
                "request_size_bytes": data.request_size_bytes,
                "response_size_bytes": data.response_size_bytes,
                "connection_frequency": data.connection_frequency,
                "domain_source": data.domain_source,
            }
        ]
    )

    predicted_label = str(model.predict(features)[0])

    return {
        "status": "success",
        "predicted_risk_level": predicted_label,
        "ml_connected": True,
    }