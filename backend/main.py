from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import pandas as pd
import os, uuid, threading, time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "temp"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
DELETE_AFTER = 300  # 5 minutes

os.makedirs(TEMP_DIR, exist_ok=True)
app.mount("/temp", StaticFiles(directory="temp"), name="temp")


def auto_delete(file_paths: list):
    time.sleep(DELETE_AFTER)
    for path in file_paths:
        if os.path.exists(path):
            os.remove(path)


@app.post("/clean-data")
async def clean_data(file: UploadFile = File(...)):
    # Validate file type
    if not file.filename.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are allowed")

    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size must be less than 5MB")

    file_id = str(uuid.uuid4())
    raw_path = f"{TEMP_DIR}/{file_id}_{file.filename}"
    clean_path = f"{TEMP_DIR}/cleaned_{file_id}_{file.filename}"

    # Save raw file
    with open(raw_path, "wb") as f:
        f.write(content)

    # Read data
    if file.filename.endswith(".csv"):
        df = pd.read_csv(raw_path)
    else:
        df = pd.read_excel(raw_path)

    rows_before = len(df)

    # Cleaning steps
    duplicates_before = df.duplicated().sum()
    df = df.drop_duplicates()

    null_rows_before = df.isnull().any(axis=1).sum()
    df = df.dropna()

    # Column formatting
    old_columns = list(df.columns)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    columns_fixed = old_columns != list(df.columns)

    rows_after = len(df)

    # Save cleaned file
    df.to_csv(clean_path, index=False)

    # Auto delete after time
    threading.Thread(target=auto_delete, args=([raw_path, clean_path],), daemon=True).start()

    return {
        "message": "Data cleaned successfully",
        "download_file": clean_path,
        "report": {
            "rows_before": rows_before,
            "rows_after": rows_after,
            "duplicates_removed": int(duplicates_before),
            "null_rows_removed": int(null_rows_before),
            "columns_standardized": columns_fixed,
            "file_auto_deleted_in_seconds": DELETE_AFTER
        }
    }
