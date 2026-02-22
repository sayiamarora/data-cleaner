Data Cleaner

Data Cleaner is an intelligent data preprocessing tool that automatically cleans, standardizes, deduplicates, and detects anomalies in CSV and Excel datasets through a smart backend engine and simple web interface.
It helps convert raw, inconsistent datasets into analysis-ready structured data with minimal manual effort.

Features

Smart Duplicate Detection
Removes duplicates even when values differ in case, spacing, formatting, or minor numeric/date variations.
Instead of exact matching, it uses normalization and similarity scoring to detect logically identical records.

Automatic Data Standardization
Column names, text values, and formats are normalized automatically to ensure consistency across the dataset.

Missing Value Handling
Rows containing incomplete or invalid data are detected and removed to improve downstream analytics quality.

ML-Based Anomaly Detection
Uses the Isolation Forest algorithm to identify abnormal numeric records, outliers, or suspicious entries.

Secure Temporary File Handling
Uploaded files are stored temporarily and automatically deleted after a defined time window using a background cleanup service.

Simple Web Interface
Users can upload datasets, view a processing report, and download the cleaned file instantly.

Processing Pipeline

The system processes data in the following order:
File validation → Dataset loading → Smart deduplication → Null removal → Column normalization → Anomaly detection → Clean export → Auto file cleanup.

Tech Stack

Backend: FastAPI, Pandas, NumPy, Scikit-learn
Algorithms: Isolation Forest, similarity matching, canonical normalization
Frontend: HTML, CSS, JavaScript

Supported Input Formats

CSV, XLSX, and XLS files are supported.

Run Locally

Install dependencies:

pip install fastapi uvicorn pandas numpy scikit-learn openpyxl

Start the backend server:

uvicorn main:app --reload

The goal of this project is to reduce manual data cleaning effort and improve dataset reliability before analytics, dashboards, or machine learning workflows.

If you want, I can also give you:
