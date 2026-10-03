# Enterprise Employee Analytics & Data Warehouse System

A complete team-ready implementation of the Greenfield mini-project from **Rising Stars - Greenfield Mini-Project - Version 2**.

## Start here

If you are working as a team, read **TEAM_START_HERE.md** first. It gives the exact first-run order and the Person 1 / Person 2 / Person 3 ownership.

## What this project implements

- Python + pandas + Faker data synthesis to create **100,000+ realistic employee-related records**.
- Normalized MySQL **OLTP** database: Employees, Departments, Projects, Assignments, Reviews.
- MySQL **OLAP Star Schema**: Fact_PerformanceReviews, Dim_Employee, Dim_Project, Dim_Date, Dim_Department.
- Surrogate keys on dimensions.
- **SCD Type 2** for employee department/role/salary history using `start_date`, `end_date`, `is_current`.
- SQL DDL, DML, Stored Procedures, CTEs and Window Functions.
- Python OOP backend with Singleton `DatabaseConnection`, entity classes and DAL/manager classes.
- Streamlit application for employee onboarding, project creation, review submission, department changes and analytics.
- Plotly dashboards for year-over-year trends, department rankings and project bottlenecks.
- Git/GitHub-friendly modular structure and editable Draw.io diagrams.

## Architecture

```text
IBM HR Dataset / Generated Seed
             |
             v
   Python Data Synthesizer
   pandas + Faker + history
             |
             v
       CSV Data Files
             |
             v
      MySQL OLTP Layer
 Employees | Departments | Projects | Assignments | Reviews
             |
             v
       ETL / Transform
 CTEs + Window Functions + SCD2
             |
             v
       MySQL OLAP Layer
       Star Schema / DW
             |
             v
       Streamlit App
 Data Entry + Analytics Dashboard
             |
             +--> OLTP writes
             |
             +--> OLAP analytical reads
```

## Project layout

```text
enterprise_employee_analytics/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── src/
│   ├── db_manager.py
│   ├── entities.py
│   ├── managers.py
│   ├── synthesizer.py
│   └── etl.py
├── scripts/
│   ├── generate_data.py
│   ├── load_oltp.py
│   ├── run_etl.py
│   └── demo_setup.py
├── sql/
│   ├── 01_create_schemas.sql
│   ├── 02_oltp_tables.sql
│   ├── 03_olap_tables.sql
│   ├── 04_stored_procedures.sql
│   └── 05_analytics_queries.sql
├── data/
│   └── README.md
├── diagrams/
│   ├── oltp_erd.drawio
│   ├── olap_star_schema.drawio
│   └── architecture.drawio
├── docs/
│   └── TEAM_WORKFLOW.md
└── tests/
    └── test_synthesizer.py
```

## 1. Prerequisites

Install:

- Python 3.10+
- MySQL Server 8.0+
- MySQL Workbench (recommended)
- Git

Create a virtual environment:

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Windows CMD

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configure MySQL

Copy `.env.example` to `.env` and edit the values:

```text
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
OLTP_DB=employee_oltp
OLAP_DB=employee_dw
```

You can create the databases/tables with the SQL files below.

## 3. Create database schemas

Open MySQL Workbench and run these files in order:

```text
sql/01_create_schemas.sql
sql/02_staging_tables.sql
sql/03_oltp_tables.sql
sql/04_olap_tables.sql
sql/05_stored_procedures.sql
```

`05_analytics_queries.sql` is for demonstrations and dashboard queries; it does not need to be run during setup.

## 4. Generate the data

The project works in two modes.

### Mode A - Use the IBM HR Analytics dataset

Download the IBM HR Analytics Employee Attrition & Performance CSV and place it at:

```text
data/WA_Fn-UseC_-HR-Employee-Attrition.csv
```

Then run:

```powershell
python scripts/generate_data.py --rows 100000
```

The synthesizer reads the IBM snapshot, scales it with Faker-generated values and engineers historical records for a subset of employees.

### Mode B - No IBM file yet

The project also has a self-contained fallback seed generator. Simply run:

```powershell
python scripts/generate_data.py --rows 100000
```

If the IBM CSV is not present, the script creates a realistic seed internally and still generates the required 100,000+ row workload. This is useful for getting the application running before the team adds the official IBM dataset.

Output files are created under `data/generated/`.

## 5. Load the OLTP database

Run:

```powershell
python scripts/load_oltp.py
```

The loader inserts departments, employees, projects, assignments and reviews in batches. It uses transactions and `executemany()` to avoid one SQL request per row.

## 6. Run ETL into the warehouse

Run:

```powershell
python scripts/run_etl.py
```

The ETL:

1. Creates/refreshes date and dimension data.
2. Loads employee history as SCD2 rows.
3. Creates project and department dimensions.
4. Loads performance-review facts.
5. Uses SQL ranking/window logic for analytical transformations.

## 7. Start Streamlit

```powershell
streamlit run app.py
```

Open the URL shown by Streamlit, normally:

```text
http://localhost:8501
```

## 8. What to test in the UI

### Employee Management

- Onboard a new employee.
- Change an existing employee's department.
- Verify the OLTP employee row changed.
- Verify `employee_dw.Dim_Employee` now has an old `is_current = 0` version and a new `is_current = 1` version.

### Projects

- Create a project.
- Assign an employee to a project.

### Reviews

- Submit a performance review.
- Run ETL again.
- Refresh the dashboard.

### Analytics

The dashboard includes:

- KPI cards for employees, reviews, average rating and total review score.
- Year-over-year average performance trends.
- Top-performing employees by department using `DENSE_RANK()`.
- Project workload/bottleneck analysis.
- Department performance comparison.

## 9. Important SCD Type 2 demonstration

Suppose employee `E10001` is currently in Engineering.

Before change:

```text
employee_sk | employee_id | department | start_date | end_date   | is_current
------------+-------------+------------+------------+------------+-----------
1           | E10001      | Engineering| 2024-01-01 | 9999-12-31 | 1
```

After the Streamlit department update to Finance:

```text
employee_sk | employee_id | department | start_date | end_date   | is_current
------------+-------------+------------+------------+------------+-----------
1           | E10001      | Engineering| 2024-01-01 | 2026-10-02 | 0
2           | E10001      | Finance    | 2026-10-03 | 9999-12-31 | 1
```

The exact dates depend on the day the change is performed.

## 10. Git team workflow

Use three feature branches:

```text
feature/person1-data-oltp
feature/person2-warehouse-etl
feature/person3-oop-streamlit
```

Each person commits only their logical module. Push the feature branch and create a Pull Request into `main`.

See `docs/TEAM_WORKFLOW.md` for the detailed split.

## 11. Cloud deployment

The application is designed for Streamlit Community Cloud. For deployment:

1. Push the repository to GitHub.
2. Add the application entry point `app.py`.
3. Add `requirements.txt`.
4. Configure secure database secrets in Streamlit's secrets/settings rather than committing `.env`.
5. Make the MySQL server reachable from the cloud environment.

For a classroom/demo deployment, a cloud-hosted MySQL-compatible database is recommended. Do not expose a local MySQL server directly to the public internet.

## 12. Troubleshooting

### `ModuleNotFoundError`

Activate the virtual environment and run:

```powershell
pip install -r requirements.txt
```

### MySQL connection refused

Check that MySQL Server is running and that `.env` has the correct host, port, username and password.

### Access denied for MySQL user

Verify the password and privileges in MySQL Workbench.

### Streamlit starts but dashboard is empty

Run, in order:

```powershell
python scripts/generate_data.py --rows 100000
python scripts/load_oltp.py
python scripts/run_etl.py
streamlit run app.py
```

### Need a clean rebuild

Drop the two project schemas in MySQL and rerun the four SQL setup files, then rerun the data load and ETL.

## 13. Evaluation checklist

- [x] 100K+ data synthesizer
- [x] Faker + pandas
- [x] Historical SCD2 data
- [x] Normalized OLTP model
- [x] Star Schema OLAP model
- [x] Dimension surrogate keys
- [x] SCD Type 2
- [x] Stored Procedures
- [x] CTEs
- [x] Window Functions / DENSE_RANK
- [x] Singleton DB connection
- [x] OOP entity classes
- [x] DAL/manager classes
- [x] Error handling
- [x] Streamlit forms
- [x] Plotly analytics
- [x] Git workflow documentation
- [x] Editable Draw.io diagrams

## Source alignment

This implementation follows the requested mini-project structure and terminology: IBM HR Analytics source, 100,000+ synthesis, normalized OLTP tables, Fact_PerformanceReviews, Dim_Employee/Project/Date/Department, SCD Type 2, advanced SQL, Python OOP, Streamlit, GitHub and Streamlit Community Cloud.

## Important: realistic demo data

The synthesizer intentionally creates meaningful variation across departments, roles, years, and project workloads. It generates multiple performance reviews per employee where possible, weighted project assignments, and 10% historical employee versions for SCD Type 2. After changing the generator, regenerate the CSVs, reload staging/OLTP, and rerun the ETL before opening the dashboard.

The dashboard also includes an **Employee Attrition Risk — Analytical Proxy**. It is a transparent demonstration score derived from warehouse signals; it is not a machine-learning prediction model.

