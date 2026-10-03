# Team Workflow — Person 1 / Person 2 / Person 3

The project statement asks for a team-built system covering synthesis, OLTP, OLAP/ETL, OOP, Streamlit and GitHub. Split the work by module so every person owns a visible technical area.

## Person 1 — Data Engineering + OLTP

Own:

- `src/synthesizer.py`
- `scripts/generate_data.py`
- `scripts/load_oltp.py`
- `sql/02_oltp_tables.sql`
- OLTP section of `diagrams/oltp_erd.drawio`

Explain in viva:

- Why Faker is needed.
- How 100K+ rows are generated without copying one row blindly.
- How historical employee versions are engineered.
- Why OLTP is normalized.
- Foreign keys and referential integrity.
- Batch inserts and transaction handling.

## Person 2 — Data Warehouse + ETL + Advanced SQL

Own:

- `src/etl.py`
- `scripts/run_etl.py`
- `sql/03_olap_tables.sql`
- `sql/04_stored_procedures.sql`
- `sql/05_analytics_queries.sql`
- `diagrams/olap_star_schema.drawio`

Explain in viva:

- Grain of Fact_PerformanceReviews.
- Surrogate vs natural keys.
- Star schema.
- SCD Type 2.
- CTE and Window Functions.
- Why `DENSE_RANK()` is used for ties.
- ETL refresh/incremental design.

## Person 3 — OOP + Streamlit + Analytics

Own:

- `src/db_manager.py`
- `src/entities.py`
- `src/managers.py`
- `app.py`
- Dashboard charts and UI.

Explain in viva:

- Singleton pattern.
- Encapsulation through entity classes.
- DAL/manager classes.
- Error handling and transactions.
- Streamlit forms.
- Why operational writes go to OLTP and analytics reads go to OLAP.
- Plotly visualizations and dashboard queries.

## Shared responsibilities

All three people should understand this complete chain:

`IBM/seed -> Faker synthesis -> CSV -> OLTP -> ETL -> Star Schema -> Streamlit`

All three should:

1. Review each other's Pull Requests.
2. Run the full setup at least once on their own machine.
3. Be able to explain SCD2, star schema, CTE, window function and Singleton.
4. Participate in final integration testing.
5. Contribute to README/presentation/documentation.

## Git branches

```text
main
├── feature/person1-data-oltp
├── feature/person2-warehouse-etl
└── feature/person3-oop-streamlit
```

Typical workflow:

```bash
git checkout main
git pull origin main
git checkout -b feature/person1-data-oltp
# work + test
git add .
git commit -m "feat: implement synthetic data and OLTP loading"
git push -u origin feature/person1-data-oltp
```

Then open a Pull Request into `main`. Do not commit `.env`, passwords or generated 100K+ CSV files.
