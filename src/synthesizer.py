"""Synthetic data generator for the Employee Analytics mini-project.

Uses the IBM HR snapshot when supplied, otherwise creates a compatible seed
with Faker so the complete project can run without a separate download.
"""
from __future__ import annotations

from pathlib import Path
from datetime import date
import random

import numpy as np
import pandas as pd
from faker import Faker

fake = Faker("en_IN")
random.seed(42)
np.random.seed(42)

DEPARTMENTS = [
    (1, "Engineering", "Bengaluru", 25000000),
    (2, "Finance", "Mumbai", 12000000),
    (3, "Human Resources", "Pune", 9000000),
    (4, "Sales", "Delhi", 18000000),
    (5, "Marketing", "Hyderabad", 11000000),
    (6, "Operations", "Chennai", 15000000),
]
ROLES = [
    "Software Engineer", "Senior Software Engineer", "Data Analyst",
    "Data Scientist", "HR Specialist", "Financial Analyst",
    "Sales Executive", "Project Manager", "Marketing Specialist",
    "Operations Analyst", "Product Manager", "Business Analyst",
]
PROJECT_NAMES = [
    "Customer Analytics Platform", "HR Modernization", "Cloud Migration",
    "Sales Intelligence", "Data Quality Program", "Employee Experience",
    "Finance Automation", "AI Recommendation Engine", "Mobile Platform",
    "Enterprise Reporting",
]


def _safe_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_seed(path: Path | None) -> pd.DataFrame:
    """Load IBM HR data if available, otherwise create a compatible seed."""
    if path and path.exists():
        df = pd.read_csv(path)
        return df

    n = 1470
    rows = []
    for i in range(n):
        age = random.randint(21, 60)
        years = random.randint(0, min(25, age - 18))
        dept_id, dept, _, _ = random.choice(DEPARTMENTS)
        rows.append({
            "EmployeeNumber": i + 1001,
            "Age": age,
            "Gender": random.choice(["Male", "Female"]),
            "Department": dept,
            "JobRole": random.choice(ROLES),
            "MonthlyIncome": random.randint(25000, 220000),
            "YearsAtCompany": years,
            "JobLevel": random.randint(1, 5),
            "PerformanceRating": random.choice([2, 3, 3, 3, 4]),
            "Attrition": random.choice(["Yes", "No", "No", "No", "No"]),
        })
    return pd.DataFrame(rows)


def _department_id(name: str) -> int:
    mapping = {d[1]: d[0] for d in DEPARTMENTS}
    return mapping.get(name, 1)


def _build_employees(seed: pd.DataFrame, count: int) -> pd.DataFrame:
    records = []
    seed = seed.reset_index(drop=True)
    for i in range(count):
        base = seed.iloc[i % len(seed)]
        employee_id = f"E{i + 1:06d}"
        department = str(base.get("Department", random.choice(DEPARTMENTS)[1]))
        if department not in {d[1] for d in DEPARTMENTS}:
            department = random.choice(DEPARTMENTS)[1]
        dept_id = _department_id(department)
        role = str(base.get("JobRole", random.choice(ROLES)))
        if not role or role == "nan":
            role = random.choice(ROLES)
        age = max(21, min(65, _safe_int(base.get("Age"), random.randint(22, 55))))
        years = max(0, min(35, _safe_int(base.get("YearsAtCompany"), random.randint(0, 15))))
        hire_year = min(2025, max(1995, 2026 - years - random.randint(0, 5)))
        if i < max(1, count // 10):
            hire_year = min(hire_year, 2022)
        # Keep the designated SCD2 population employed long enough to have
        # genuine historical (2024) review records.
        hire_end_year = 2023 if i < max(1, count // 10) else 2025
        hire_end_year = max(hire_year, hire_end_year)
        hire_date = fake.date_between(start_date=date(hire_year, 1, 1), end_date=date(hire_end_year, 12, 31))
        salary = _safe_float(base.get("MonthlyIncome"), random.randint(30000, 180000)) * 12
        if salary < 240000:
            salary = random.randint(30000, 180000) * 12
        records.append({
            "employee_id": employee_id,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": f"{employee_id.lower()}@example.com",
            "gender": str(base.get("Gender", random.choice(["Male", "Female"]))),
            "age": age,
            "department_id": dept_id,
            "department_name": department,
            "role": role,
            "salary": round(salary, 2),
            "hire_date": hire_date,
            "status": "Active" if str(base.get("Attrition", "No")) != "Yes" else random.choice(["Active", "Resigned"]),
        })
    return pd.DataFrame(records)


def _build_projects() -> pd.DataFrame:
    records = []
    for i, name in enumerate(PROJECT_NAMES, start=1):
        start = pd.Timestamp("2024-01-01") + pd.Timedelta(days=(i - 1) * 45)
        records.append({
            "project_id": f"P{i:04d}",
            "project_name": name,
            "description": f"Enterprise initiative: {name}",
            "start_date": start.date(),
            "end_date": (start + pd.Timedelta(days=random.randint(180, 540))).date(),
            "status": random.choice(["Planned", "Active", "Active", "Completed"]),
        })
    return pd.DataFrame(records)


def generate_data(output_dir: str, rows: int = 100_000, ibm_path: str | None = None) -> dict[str, int]:
    """Generate a realistic, analytical HR dataset at 100K+ scale.

    The generator deliberately creates meaningful variation so the warehouse
    dashboards show trends instead of six departments/projects having almost
    identical averages. It creates multiple reviews per employee across years,
    weighted project workloads, and a 10% SCD Type-2 history population.
    """
    if rows < 100_000:
        rows = 100_000
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    seed = load_seed(Path(ibm_path) if ibm_path else None)
    employees = _build_employees(seed, rows)
    departments = pd.DataFrame([
        {"department_id": d[0], "department_name": d[1], "location": d[2], "budget": d[3]}
        for d in DEPARTMENTS
    ])
    projects = _build_projects()

    # ------------------------------------------------------------------
    # Employee-level performance profile.
    # This creates realistic differences between departments/roles while
    # retaining randomness at the individual-review level.
    # ------------------------------------------------------------------
    dept_base = {
        1: 84.0,  # Engineering
        2: 76.0,  # Finance
        3: 79.0,  # Human Resources
        4: 68.0,  # Sales
        5: 81.0,  # Marketing
        6: 73.0,  # Operations
    }
    role_effect = {
        "Data Scientist": 5.0,
        "Senior Software Engineer": 4.0,
        "Software Engineer": 2.0,
        "Project Manager": 3.0,
        "Product Manager": 2.5,
        "Business Analyst": 1.0,
        "Data Analyst": 1.0,
        "Financial Analyst": 0.5,
        "Marketing Specialist": 1.0,
        "HR Specialist": 0.0,
        "Operations Analyst": -1.0,
        "Sales Executive": -2.0,
    }
    employees["performance_base"] = employees.apply(
        lambda r: dept_base.get(int(r["department_id"]), 72.0)
        + role_effect.get(str(r["role"]), 0.0)
        + np.random.normal(0, 5), axis=1
    ).clip(45, 95)

    # ------------------------------------------------------------------
    # Projects have deliberately different workload weights. This makes
    # project bottleneck analysis useful instead of perfectly uniform.
    # ------------------------------------------------------------------
    project_weights = np.array([0.08, 0.14, 0.22, 0.10, 0.06, 0.08, 0.07, 0.15, 0.04, 0.06])
    project_weights = project_weights / project_weights.sum()
    project_ids = projects["project_id"].to_numpy()

    # Two assignments for a subset of employees; primary assignments are
    # weighted toward a few major initiatives.
    primary_projects = np.random.choice(project_ids, rows, p=project_weights)
    secondary_mask = np.random.random(rows) < 0.35
    secondary_count = int(secondary_mask.sum())
    secondary_projects = np.random.choice(project_ids, secondary_count, p=project_weights)

    assignments_primary = pd.DataFrame({
        "assignment_id": [f"A{i+1:07d}" for i in range(rows)],
        "employee_id": employees["employee_id"].values,
        "project_id": primary_projects,
        "assignment_role": employees["role"].values,
        "start_date": employees["hire_date"].values,
        "end_date": [pd.NaT] * rows,
    })

    if secondary_count:
        secondary_employees = employees.loc[secondary_mask].copy()
        assignments_secondary = pd.DataFrame({
            "assignment_id": [f"A{rows+i+1:07d}" for i in range(secondary_count)],
            "employee_id": secondary_employees["employee_id"].values,
            "project_id": secondary_projects,
            "assignment_role": ["Cross-functional Member"] * secondary_count,
            "start_date": secondary_employees["hire_date"].values,
            "end_date": [pd.NaT] * secondary_count,
        })
        assignments = pd.concat([assignments_primary, assignments_secondary], ignore_index=True)
    else:
        assignments = assignments_primary

    # ------------------------------------------------------------------
    # Three review periods where possible. Employees with historical SCD2
    # versions get a 2024 review plus 2025/2026 reviews. Newer hires receive
    # reviews only after their hire date.
    # ------------------------------------------------------------------
    history_count = max(1, rows // 10)
    employee_ids = employees["employee_id"].to_numpy()
    hire_dates = pd.to_datetime(employees["hire_date"])
    primary_project_series = pd.Series(primary_projects, index=employees.index)

    review_frames = []
    review_counter = 1
    review_years = [2024, 2025, 2026]
    for year in review_years:
        eligible = employees.index[hire_dates.dt.year <= year]
        if len(eligible) == 0:
            continue

        # Keep historical employees represented in 2024, while 2025/2026
        # reviews cover the broader active workforce.
        if year == 2024:
            eligible = employees.index[:history_count]

        n = len(eligible)
        hire_subset = hire_dates.loc[eligible]
        year_start = pd.Timestamp(f"{year}-01-15")
        year_end = pd.Timestamp(f"{year}-12-15")
        # Every review is placed inside its labelled calendar year, unless
        # an employee was hired after the beginning of that year.
        starts = hire_subset.where(hire_subset > year_start, year_start)
        starts = starts.clip(upper=year_end)
        span_days = (year_end - starts).dt.days.to_numpy()
        offsets = np.array([np.random.randint(0, max(1, int(days) + 1)) for days in span_days])
        review_dates = (starts + pd.to_timedelta(offsets, unit="D")).dt.date.tolist()

        # Historical department effect for the 2024 SCD population.
        dept_ids = employees.loc[eligible, "department_id"].astype(int).to_numpy()
        if year == 2024:
            dept_ids = ((dept_ids % len(DEPARTMENTS)) + 1)
        bases = np.array([dept_base.get(int(d), 72.0) for d in dept_ids])
        role_effects = np.array([role_effect.get(str(r), 0.0) for r in employees.loc[eligible, "role"]])
        individual = employees.loc[eligible, "performance_base"].to_numpy()
        # Historical reviews are a little lower before the simulated changes.
        year_effect = {2024: -3.0, 2025: 0.0, 2026: 2.0}[year]
        scores = np.clip(individual * 0.55 + bases * 0.35 + role_effects * 0.10 + year_effect
                          + np.random.normal(0, 7, n), 35, 99)
        ratings = np.clip(np.rint(scores / 20), 1, 5).astype(int)

        # Mostly primary projects; a smaller share uses a secondary assignment.
        projects_for_reviews = primary_project_series.loc[eligible].to_numpy().copy()
        if secondary_count:
            employee_to_secondary = dict(zip(
                employees.loc[secondary_mask, "employee_id"],
                assignments_secondary["project_id"]
            ))
            for pos, idx in enumerate(eligible):
                eid = employees.loc[idx, "employee_id"]
                if eid in employee_to_secondary and random.random() < 0.25:
                    projects_for_reviews[pos] = employee_to_secondary[eid]

        frame = pd.DataFrame({
            "review_id": [f"R{review_counter+i:07d}" for i in range(n)],
            "employee_id": employees.loc[eligible, "employee_id"].to_numpy(),
            "project_id": projects_for_reviews,
            "review_date": review_dates,
            "rating": ratings,
            "review_score": np.round(scores, 2),
            "comments": [f"{year} performance review" for _ in range(n)],
        })
        review_frames.append(frame)
        review_counter += n

    reviews = pd.concat(review_frames, ignore_index=True)

    # Final guardrail: review rows labelled by year must physically belong to
    # that calendar year. This keeps the Date dimension and YoY dashboard
    # clean even when source hire dates are unusual.
    reviews["review_date"] = pd.to_datetime(reviews["review_date"])
    for review_year in (2024, 2025, 2026):
        mask = reviews["comments"].eq(f"{review_year} performance review")
        bad = mask & (reviews["review_date"].dt.year != review_year)
        if bad.any():
            count_bad = int(bad.sum())
            replacement = pd.Timestamp(f"{review_year}-01-15") + pd.to_timedelta(
                np.random.randint(0, 334, count_bad), unit="D"
            )
            reviews.loc[bad, "review_date"] = replacement.values
    reviews["review_date"] = reviews["review_date"].dt.date

    # ------------------------------------------------------------------
    # SCD2 history: 10% of employees have an earlier department/role/salary
    # version. Current records remain in employees.csv.
    # ------------------------------------------------------------------
    history_source = employees.iloc[:history_count].copy()
    history_source["department_id"] = history_source["department_id"].apply(
        lambda x: ((int(x) % len(DEPARTMENTS)) + 1)
    )
    history_source["department_name"] = history_source["department_id"].map(
        {d[0]: d[1] for d in DEPARTMENTS}
    )
    history_source["role"] = np.random.choice(ROLES, history_count)
    history_source["salary"] = np.round(history_source["salary"] * np.random.uniform(0.78, 0.92, history_count), 2)
    history_source["start_date"] = pd.to_datetime(history_source["hire_date"]) + pd.to_timedelta(
        np.maximum(30, np.minimum(500, np.random.randint(30, 900, history_count))), unit="D"
    )
    history_source["start_date"] = history_source["start_date"].clip(upper=pd.Timestamp("2024-06-01"))
    history_source["end_date"] = pd.to_datetime("2024-12-31")
    history_source["is_current"] = False
    history = history_source[["employee_id", "department_id", "department_name", "role", "salary", "start_date", "end_date", "is_current"]]

    # Guarantee that every historical employee has a 2024 review date that
    # falls inside its historical SCD2 validity window.
    history_start_map = dict(zip(history["employee_id"], pd.to_datetime(history["start_date"])))
    hist_review_mask = reviews["employee_id"].isin(history["employee_id"]) & reviews["review_date"].astype(str).str.startswith("2024")
    for idx in reviews.index[hist_review_mask]:
        eid = reviews.at[idx, "employee_id"]
        start = max(history_start_map[eid], pd.Timestamp("2024-01-15"))
        end = pd.Timestamp("2024-12-15")
        if start > end:
            start = pd.Timestamp("2024-01-15")
        reviews.at[idx, "review_date"] = (start + pd.Timedelta(days=int(np.random.randint(0, max(1, (end-start).days + 1))))).date()

    # Keep helper columns out of the OLTP CSV.
    employees = employees.drop(columns=["performance_base"])

    departments.to_csv(out / "departments.csv", index=False)
    employees.to_csv(out / "employees.csv", index=False)
    projects.to_csv(out / "projects.csv", index=False)
    assignments.to_csv(out / "assignments.csv", index=False)
    reviews.to_csv(out / "reviews.csv", index=False)
    history.to_csv(out / "employee_history.csv", index=False)

    return {
        "employees": len(employees),
        "departments": len(departments),
        "projects": len(projects),
        "assignments": len(assignments),
        "reviews": len(reviews),
        "historical_employee_versions": len(history),
        "total_generated_rows": len(employees) + len(departments) + len(projects) + len(assignments) + len(reviews) + len(history),
    }
