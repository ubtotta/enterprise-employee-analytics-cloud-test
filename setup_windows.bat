@echo off
setlocal
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env
python scripts\generate_data.py --rows 100000
python scripts\load_oltp.py
python scripts\run_etl.py
streamlit run app.py
