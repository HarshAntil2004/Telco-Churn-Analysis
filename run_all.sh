#!/usr/bin/env bash
set -e
pip install -r requirements.txt
python src/01_clean_and_load.py
python src/02_run_sql.py
python src/03_analysis_and_model.py
