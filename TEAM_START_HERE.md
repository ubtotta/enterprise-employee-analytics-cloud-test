# Team Start Here — First Run

## Before you touch the code

There are three owners:

- **Person 1:** data synthesis + staging + OLTP
- **Person 2:** warehouse + ETL + SQL
- **Person 3:** OOP + Streamlit + analytics

Do not try to understand every file on day one. First get the pipeline running once. Then study one layer at a time.

## First run checklist

### Step 1 — Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 2 — Configure

```powershell
copy .env.example .env
```

Edit `.env` with your MySQL password.

### Step 3 — Build MySQL schemas

Run in MySQL Workbench:

```text
sql/01_create_schemas.sql
sql/02_staging_tables.sql
sql/03_oltp_tables.sql
sql/04_olap_tables.sql
sql/05_stored_procedures.sql
```

### Step 4 — Generate 100K+ rows

```powershell
python scripts/generate_data.py --rows 100000
```

### Step 5 — Load staging + OLTP

```powershell
python scripts/load_oltp.py
```

### Step 6 — Run warehouse ETL

```powershell
python scripts/run_etl.py
```

### Step 7 — Start application

```powershell
streamlit run app.py
```

## What each person should verify

### Person 1

Run SQL:

```sql
SELECT COUNT(*) FROM employee_staging.staging_employees;
SELECT COUNT(*) FROM employee_oltp.Employees;
SELECT COUNT(*) FROM employee_oltp.Reviews;
```

### Person 2

Run:

```sql
SELECT COUNT(*) FROM employee_dw.Dim_Employee;
SELECT COUNT(*) FROM employee_dw.Fact_PerformanceReviews;
SELECT employee_id, COUNT(*) versions
FROM employee_dw.Dim_Employee
GROUP BY employee_id
HAVING COUNT(*) > 1
LIMIT 10;
```

That last query demonstrates SCD2 history.

### Person 3

Open Streamlit and test:

1. Dashboard
2. Onboard Employee
3. Create Project
4. Assign Employee
5. Submit Review
6. Change Department
7. Refresh and inspect analytics

## The most important viva story

> "We start with the IBM HR snapshot or a compatible seed, use pandas and Faker to synthesize a 100K+ workload and engineer employee history. The data first enters a MySQL staging schema, then a normalized OLTP model. Python/SQL ETL transforms the operational data into a Star Schema with surrogate keys and SCD Type 2 employee history. The Streamlit OOP application writes operational changes to OLTP and reads analytical results from OLAP. Advanced SQL uses CTEs, window functions and stored procedures."

Learn this flow before memorizing individual code lines.
