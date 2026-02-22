from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

from difflib import SequenceMatcher
import os, uuid, time, threading, re, unicodedata

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "temp"
MAX_FILE_SIZE = 10 * 1024 * 1024
FILE_LIFETIME = 300

os.makedirs(TEMP_DIR, exist_ok=True)
app.mount("/temp", StaticFiles(directory="temp"), name="temp")


# ---------- AUTO CLEANUP ----------
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


# ---------- NORMALIZATION ----------
def normalize(val):
    if pd.isna(val):
        return ""

    val = str(val)
    val = unicodedata.normalize("NFKD", val)
    val = re.sub(r"[\u200B-\u200D\uFEFF]", "", val)
    val = re.sub(r"\s+", " ", val)
    val = val.strip().lower()

    # normalize numbers
    try:
        return str(round(float(val), 4))
    except:
        pass

    # normalize dates
    try:
        dt = pd.to_datetime(val, errors="raise")
        return dt.strftime("%Y-%m-%d")
    except:
        pass

    return val


# ---------- SIMILARITY FUNCTION ----------
def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


# ---------- RECORD MATCHING ----------
def records_match(row1, row2, threshold=0.92):
    score = 0
    weight_sum = 0

    for col in row1.index:

        v1 = normalize(row1[col])
        v2 = normalize(row2[col])

        # numeric tolerance
        try:
            if abs(float(v1) - float(v2)) <= 1:
                score += 1.2
                weight_sum += 1.2
                continue
        except:
            pass

        # date tolerance
        try:
            d1 = pd.to_datetime(v1)
            d2 = pd.to_datetime(v2)
            if abs((d1 - d2).days) <= 3:
                score += 1.2
                weight_sum += 1.2
                continue
        except:
            pass

        # text similarity
        sim = similarity(v1, v2)
        score += sim
        weight_sum += 1

    return (score / weight_sum) >= threshold


# ---------- SMART DEDUP ENGINE ----------
def smart_deduplicate(df):

    keep_rows = []
    used = set()

    for i in range(len(df)):
        if i in used:
            continue

        base = df.iloc[i]
        duplicates = [i]

        for j in range(i+1, len(df)):
            if j in used:
                continue

            if records_match(base, df.iloc[j]):
                duplicates.append(j)

        # choose best record (least nulls)
        best = min(duplicates, key=lambda x: df.iloc[x].isnull().sum())
        keep_rows.append(best)

        for d in duplicates:
            used.add(d)

    return df.iloc[keep_rows]


# ---------- API ----------
@app.post("/clean-data")
async def clean_data(file: UploadFile = File(...)):

    if not file.filename.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only CSV/Excel allowed")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    file_id = str(uuid.uuid4())
    raw_path = f"{TEMP_DIR}/{file_id}_{file.filename}"
    clean_path = f"{TEMP_DIR}/cleaned_{file_id}.csv"

    with open(raw_path, "wb") as f:
        f.write(content)

    # LOAD FILE
    if file.filename.endswith(".csv"):
        df = pd.read_csv(raw_path)
    else:
        df = pd.read_excel(raw_path)

    rows_before = len(df)

    # ---------- SMART DEDUP ----------
    df = smart_deduplicate(df)
    duplicates_removed = rows_before - len(df)

    # ---------- NULL CLEAN ----------
    null_rows_removed = df.isnull().any(axis=1).sum()
    df = df.dropna()

    # ---------- COLUMN STANDARDIZATION ----------
    old_cols = list(df.columns)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    columns_fixed = old_cols != list(df.columns)

    # ---------- ANOMALY DETECTION ----------
    numeric_df = df.select_dtypes(include=[np.number])
    anomalies_removed = 0

    if not numeric_df.empty:
        model = IsolationForest(contamination=0.02, random_state=42)
        preds = model.fit_predict(numeric_df)
        mask = preds == -1
        anomalies_removed = mask.sum()
        df = df[~mask]

    rows_after = len(df)

    df.to_csv(clean_path, index=False)

    return {
        "message": "Smart cleaning complete",
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