from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

import os, uuid, time, threading

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "temp"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
FILE_LIFETIME = 300  # 5 minutes

os.makedirs(TEMP_DIR, exist_ok=True)
app.mount("/temp", StaticFiles(directory="temp"), name="temp")


# -------- AUTO CLEANUP SERVICE --------
def cleanup_job():
    while True:
        now = time.time()
        for file in os.listdir(TEMP_DIR):
            path = os.path.join(TEMP_DIR, file)
            if os.path.isfile(path):
                if now - os.path.getmtime(path) > FILE_LIFETIME:
                    os.remove(path)
        time.sleep(60)

threading.Thread(target=cleanup_job, daemon=True).start()


# -------- CLEANING ENDPOINT --------
@app.post("/clean-data")
async def clean_data(file: UploadFile = File(...)):

    # Validate file type
    if not file.filename.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only CSV/Excel allowed")

    # Validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    # Save file
    file_id = str(uuid.uuid4())
    raw_path = f"{TEMP_DIR}/{file_id}_{file.filename}"
    clean_path = f"{TEMP_DIR}/cleaned_{file_id}.csv"

    with open(raw_path, "wb") as f:
        f.write(content)

    # -------- LOAD FILE --------
    if file.filename.endswith(".csv"):
        df = pd.read_csv(raw_path)
    else:
        df = pd.read_excel(raw_path)

    rows_before = len(df)

    # -------- SMART DUPLICATE DETECTION --------
    df_normalized = df.copy()

    for col in df_normalized.columns:
        if df_normalized[col].dtype == "object":
            df_normalized[col] = (
                df_normalized[col]
                .astype(str)
                .str.strip()
                .str.lower()
                .str.replace(r"\s+", " ", regex=True)
            )

    duplicate_mask = df_normalized.duplicated()
    duplicates_removed = duplicate_mask.sum()
    df = df.loc[~duplicate_mask].copy()

    # -------- NULL HANDLING --------
    null_rows_removed = df.isnull().any(axis=1).sum()
    df = df.dropna()

    # -------- COLUMN STANDARDIZATION --------
    old_cols = list(df.columns)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    columns_fixed = old_cols != list(df.columns)

    # -------- TYPE NORMALIZATION --------
    for col in df.columns:
        try:
            df[col] = pd.to_datetime(df[col])
        except:
            pass

    # -------- ANOMALY DETECTION --------
    numeric_df = df.select_dtypes(include=[np.number])
    anomalies_removed = 0

    if not numeric_df.empty:
        model = IsolationForest(contamination=0.02, random_state=42)
        preds = model.fit_predict(numeric_df)
        mask = preds == -1
        anomalies_removed = mask.sum()
        df = df[~mask]

    rows_after = len(df)

    # -------- SAVE CLEAN FILE --------
    df.to_csv(clean_path, index=False)

    return {
        "message": "Data cleaned successfully",
        "download_file": clean_path,
        "report": {
            "rows_before": rows_before,
            "rows_after": rows_after,
            "duplicates_removed": int(duplicates_removed),
            "null_rows_removed": int(null_rows_removed),
            "columns_standardized": columns_fixed,
            "anomalies_removed": int(anomalies_removed),
            "file_auto_deleted_in_seconds": FILE_LIFETIME
        }
    }