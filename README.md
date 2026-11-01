# Smart Pharmaceutical Manufacturing Quality Monitoring Platform

A small educational Flask + SQLite application demonstrating batch tracking, process readings, rule-based deviation alerts, audit records and batch reports.

## Demo process limits
The example uses temperature 20-25 °C, humidity 30-60%, and pressure 95-105 kPa. These are illustrative values only. They are NOT validated pharmaceutical specifications. A real system must use approved product- and process-specific limits.

## Run locally
```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
Open http://localhost:5000

## Run with Docker
```bash
docker compose up --build
```
Open http://localhost:5000. Stop with `docker compose down`.

## Main features
- Create and track production batches
- Record temperature, humidity, pressure and equipment condition
- Generate alerts when demo limits are exceeded
- Maintain an audit trail
- Generate a batch quality summary

Educational prototype only; not validated for GMP production or regulatory use.
