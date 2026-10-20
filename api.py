
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(
    title="Android Network Traffic ML API",
    description="Local API for network traffic analysis research",
    version="1.0.0",
)


class TrafficData(BaseModel):
    protocol: str
    port: int = Field(ge=1, le=65535)
    request_size_bytes: int = Field(ge=0)
    response_size_bytes: int = Field(ge=0)
    connection_frequency: int = Field(ge=0)
    domain_source: str


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
        "status": "healthy"
    }


@app.post("/predict")
def predict(data: TrafficData):
    return {
        "status": "success",
        "message": "Request received successfully. ML model is not connected yet.",
        "received_data": data.model_dump(),
        "ml_connected": False,
    }
