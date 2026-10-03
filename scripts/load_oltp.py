from __future__ import annotations

from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import settings
from src.db_manager import DatabaseConnection

DATA = ROOT / "data" / "generated"
BATCH = 5000


def _mysql_safe(value):
    """Convert pandas missing values (NaN/NaT) to SQL NULL (None)."""
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def insert_batches(cur, sql, rows):
    # pandas uses NaN/NaT for missing values. Passing those directly to
    # mysql-connector can make MySQL interpret `nan` as a column/expression.
    # Convert every missing scalar to Python None so MySQL receives NULL.
    rows = [tuple(_mysql_safe(value) for value in row) for row in rows]
    for i in range(0, len(rows), BATCH):
        cur.executemany(sql, rows[i:i+BATCH])
        print(f"  inserted {min(i+BATCH, len(rows)):,}/{len(rows):,}")


def load_staging(db, departments, employees, projects, assignments, reviews, history):
    conn = db.connect(settings.staging_db)
    try:
        cur = conn.cursor()
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        for table in ["staging_reviews", "staging_assignments", "staging_projects", "staging_employees", "staging_departments", "staging_employee_history"]:
            cur.execute(f"TRUNCATE TABLE {table}")
        cur.execute("SET FOREIGN_KEY_CHECKS=1")
        insert_batches(cur, "INSERT INTO staging_departments VALUES (%s,%s,%s,%s)", departments[["department_id","department_name","location","budget"]].itertuples(index=False, name=None))
        insert_batches(cur, "INSERT INTO staging_employees VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", employees[["employee_id","first_name","last_name","email","gender","age","department_id","department_name","role","salary","hire_date","status"]].itertuples(index=False, name=None))
        insert_batches(cur, "INSERT INTO staging_projects VALUES (%s,%s,%s,%s,%s,%s)", projects[["project_id","project_name","description","start_date","end_date","status"]].itertuples(index=False, name=None))
        insert_batches(cur, "INSERT INTO staging_assignments VALUES (%s,%s,%s,%s,%s,%s)", assignments[["assignment_id","employee_id","project_id","assignment_role","start_date","end_date"]].itertuples(index=False, name=None))
        insert_batches(cur, "INSERT INTO staging_reviews VALUES (%s,%s,%s,%s,%s,%s,%s)", reviews[["review_id","employee_id","project_id","review_date","rating","review_score","comments"]].itertuples(index=False, name=None))
        insert_batches(cur, "INSERT INTO staging_employee_history VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", history[["employee_id","department_id","department_name","role","salary","start_date","end_date","is_current"]].itertuples(index=False, name=None))
        conn.commit()
        print("Staging load completed.")
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


def main():
    required = [DATA / f for f in ["departments.csv","employees.csv","projects.csv","assignments.csv","reviews.csv"]]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing files. Run scripts/generate_data.py first:\n" + "\n".join(missing))

    departments = pd.read_csv(DATA / "departments.csv")
    employees = pd.read_csv(DATA / "employees.csv")
    projects = pd.read_csv(DATA / "projects.csv")
    assignments = pd.read_csv(DATA / "assignments.csv")
    reviews = pd.read_csv(DATA / "reviews.csv")
    history = pd.read_csv(DATA / "employee_history.csv")

    db = DatabaseConnection()
    print("Loading generated data into MySQL staging schema...")
    load_staging(db, departments, employees, projects, assignments, reviews, history)
    conn = db.connect(settings.oltp_db)
    try:
        cur = conn.cursor()
        # Clean child tables first for repeatable local setup.
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        for table in ["Reviews", "Assignments", "Projects", "Employees", "Departments"]:
            cur.execute(f"TRUNCATE TABLE {table}")
        cur.execute("SET FOREIGN_KEY_CHECKS=1")

        print("Loading Departments...")
        insert_batches(cur, "INSERT INTO Departments(department_id,department_name,location,budget) VALUES (%s,%s,%s,%s)",
                       departments[["department_id","department_name","location","budget"]].itertuples(index=False, name=None))
        print("Loading Employees...")
        insert_batches(cur, """INSERT INTO Employees(employee_id,first_name,last_name,email,gender,age,department_id,role,salary,hire_date,status)
                              VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                       employees[["employee_id","first_name","last_name","email","gender","age","department_id","role","salary","hire_date","status"]].itertuples(index=False, name=None))
        print("Loading Projects...")
        insert_batches(cur, "INSERT INTO Projects(project_id,project_name,description,start_date,end_date,status) VALUES (%s,%s,%s,%s,%s,%s)",
                       projects[["project_id","project_name","description","start_date","end_date","status"]].itertuples(index=False, name=None))
        print("Loading Assignments...")
        insert_batches(cur, "INSERT INTO Assignments(assignment_id,employee_id,project_id,assignment_role,start_date,end_date) VALUES (%s,%s,%s,%s,%s,%s)",
                       assignments[["assignment_id","employee_id","project_id","assignment_role","start_date","end_date"]].itertuples(index=False, name=None))
        print("Loading Reviews...")
        insert_batches(cur, "INSERT INTO Reviews(review_id,employee_id,project_id,review_date,rating,review_score,comments) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                       reviews[["review_id","employee_id","project_id","review_date","rating","review_score","comments"]].itertuples(index=False, name=None))
        conn.commit()
        print("\nOLTP load completed successfully.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
