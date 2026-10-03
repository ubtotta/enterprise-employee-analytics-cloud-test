install:
	python -m pip install -r requirements.txt

synthesize:
	python scripts/generate_data.py --rows 100000

load:
	python scripts/load_oltp.py

etl:
	python scripts/run_etl.py

app:
	streamlit run app.py

test:
	pytest -q
