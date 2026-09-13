# Public Archive Digitization Prioritizer

A 100% local, CSV-first Streamlit dashboard for transparent preservation screening.

## Features
- Explainable 0–100 digitization priority score
- Low / Moderate / High / Critical classification
- Preservation review queue and interactive explorer
- Condition, historical value, public demand and language rarity analytics
- Physical-risk, metadata and catalog-completeness analysis
- Collection and language benchmarking
- What-if preservation scenario lab
- Data-quality/readiness view
- Filtered CSV export
- No external APIs or cloud services required

## Run
```bash
cd Public-Archive-Digitization-Prioritizer
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## CSV
The included sample is `data/sample_public_archive_records.csv`.
The dashboard validates all required columns before accepting a custom CSV.

## Responsible use
Scores are screening indicators only. They do not establish archival significance, legal obligations, conservation outcomes, or preservation standards.
