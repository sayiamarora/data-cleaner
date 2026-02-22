🚀 Features
✔ Smart Duplicate Detection

Removes duplicates even when values differ in:

Case sensitivity (John vs john)

Spacing or hidden characters

Date formats

Numeric formats

Minor value variations

Uses similarity scoring and normalization instead of exact matching.

✔ Data Standardization

Cleans column names

Normalizes formats

Removes inconsistent spacing

Handles mixed data types

✔ Missing Value Handling

Detects incomplete rows

Removes invalid records automatically

✔ Anomaly Detection (ML-based)

Uses Isolation Forest to detect outliers such as:

Suspicious numeric values

Entry errors

Abnormal records

✔ Secure Temporary Storage

Uploaded files auto-delete after processing window

Background cleanup service prevents data persistence

✔ Simple Web UI

Upload CSV/Excel

View cleaning report

Download cleaned dataset

🧠 Processing Pipeline

File validation & upload

Dataset loading

Smart duplicate resolution

Null record removal

Column normalization

ML anomaly detection

Clean dataset export

Auto file cleanup

🏗️ Tech Stack

Backend

FastAPI

Pandas

NumPy

Scikit-learn

Algorithms

Isolation Forest (outlier detection)

Weighted similarity matching

Canonical data normalization

Frontend

HTML, CSS, JavaScript

📂 Supported Inputs

.csv

.xlsx

.xls
