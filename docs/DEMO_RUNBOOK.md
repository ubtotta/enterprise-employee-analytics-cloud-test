# Project Demonstration Runbook

## 1. One-sentence project explanation

This project is an end-to-end employee analytics platform that generates large HR data, stores operational data in a normalized MySQL OLTP database, transforms it through ETL/SCD Type 2 into a Star Schema warehouse, and serves data-entry and executive analytics through Streamlit.

## 2. Pipeline to demonstrate

Python + Faker
→ CSV synthetic data
→ MySQL staging
→ MySQL OLTP
→ Python/SQL ETL
→ OLAP Star Schema + SCD Type 2
→ Streamlit
→ Plotly analytics

## 3. Recommended demonstration order

1. Show the architecture diagram.
2. Show generated CSV row counts (100K+ employees, 200K+ reviews, 10K historical versions).
3. Show OLTP tables in MySQL Workbench.
4. Show OLAP Star Schema tables.
5. Demonstrate SCD Type 2 with one employee: old version becomes `is_current = FALSE`, new version becomes `TRUE`.
6. Show the ETL SQL using a CTE and a window function.
7. Open Streamlit and show KPI cards.
8. Show YoY performance trend.
9. Show department performance differences.
10. Show project workload/bottleneck differences.
11. Show the attrition-risk analytical proxy and clearly state that it is a transparent rule-based demo, not a trained ML model.
12. Demonstrate onboarding a new employee, creating a project, and submitting a review.
13. Demonstrate a department change through the UI and verify the new SCD2 row in the warehouse.

## 4. Regeneration after the realistic-data update

Run these in order:

```powershell
python scripts/generate_data.py --rows 100000
python scripts/load_oltp.py
python scripts/run_etl.py
streamlit run app.py
```

Do not skip the data generation step after updating the synthesizer. The dashboard reads the MySQL warehouse, so the new CSV data must be loaded and the warehouse refreshed before the visualizations change.

## 5. What the new synthetic data is designed to show

- 100,000 employees.
- About 135,000 project assignments.
- About 210,000 performance reviews across 2024, 2025, and 2026.
- 10,000 historical employee versions for SCD Type 2.
- Department performance differences instead of identical averages.
- Weighted project workloads instead of uniform project counts.
- Year-over-year performance movement.
- A transparent attrition-risk proxy based on warehouse signals.
