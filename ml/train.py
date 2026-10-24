from pathlib import Path
import warnings

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from sklearn.metrics import accuracy_score


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "training_dataset.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "traffic_classifier.joblib"

FEATURES = [
    "protocol",
    "port",
    "request_size_bytes",
    "response_size_bytes",
    "connection_frequency",
    "domain_source",
]

NUMERIC_FEATURES = [
    "port",
    "request_size_bytes",
    "response_size_bytes",
    "connection_frequency",
]

CATEGORICAL_FEATURES = [
    "protocol",
    "domain_source",
]

TARGET = "risk_level"


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}\n"
            "Put your CSV at data/training_dataset.csv."
        )

    df = pd.read_csv(DATA_PATH)

    required_columns = FEATURES + [TARGET]
    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required CSV columns: {missing_columns}"
        )

    df = df[required_columns].copy()
    df[TARGET] = df[TARGET].astype("string").str.strip()
    df = df.dropna(subset=[TARGET])
    df = df[df[TARGET] != ""]

    for column in NUMERIC_FEATURES:
        df[column] = pd.to_numeric(
            df[column], errors="coerce"
        )

    for column in CATEGORICAL_FEATURES:
        df[column] = df[column].astype("string")
        df[column] = df[column].replace(
            {"": pd.NA, "nan": pd.NA, "None": pd.NA}
        )

    if len(df) < 2:
        raise ValueError("At least two labelled rows are required.")

    class_counts = df[TARGET].value_counts()

    if len(class_counts) < 2:
        raise ValueError(
            "Training requires at least two different risk_level labels."
        )

    print("\nDataset summary")
    print("----------------")
    print(f"Rows used: {len(df)}")
    print(f"Features: {', '.join(FEATURES)}")
    print("\nLabel counts:")
    print(class_counts.to_string())

    if len(df) < 100:
        warnings.warn(
            "This dataset is very small. This run checks the training "
            "pipeline only; it cannot establish reliable model performance."
        )

    X = df[FEATURES]
    y = df[TARGET].astype(str)

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="most_frequent"),
            ),
            (
                "encoder",
                OneHotEncoder(handle_unknown="ignore"),
            ),
        ]
    )

    preprocessing = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            (
                "categorical",
                categorical_pipeline,
                CATEGORICAL_FEATURES,
            ),
        ]
    )

    classifier = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        class_weight="balanced",
    )

    model = Pipeline(
        steps=[
            ("preprocessing", preprocessing),
            ("classifier", classifier),
        ]
    )

    model.fit(X, y)

    # This is training-set fit accuracy, NOT held-out test accuracy.
    fitted_predictions = model.predict(X)
    fit_accuracy = accuracy_score(y, fitted_predictions)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, MODEL_PATH)

    print("\nTraining finished.")
    print(f"Model saved to: {MODEL_PATH}")
    print(f"Training-set fit accuracy: {fit_accuracy:.3f}")
    print(
        "Warning: training-set accuracy is not evidence of "
        "generalization or real-world malware detection."
    )


if __name__ == "__main__":
    main()