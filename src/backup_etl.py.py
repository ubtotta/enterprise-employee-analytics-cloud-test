"""Python ETL from normalized OLTP CSV/data to MySQL Star Schema."""
from __future__ import annotations

from pathlib import Path
from datetime import date
import pandas as pd

from config import settings
from src.db_manager import DatabaseConnection


class EmployeeWarehouseETL:
    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        self.db = DatabaseConnection()

    def _read(self, name: str) -> pd.DataFrame:
        path = self.data_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Missing generated file: {path}. Run scripts/generate_data.py first.")
        return pd.read_csv(path)

    @staticmethod
    def _date_key(value) -> int:
        return int(pd.Timestamp(value).strftime("%Y%m%d"))

    def run(self, refresh: bool = True):
        employees = self._read("employees.csv")
        departments = self._read("departments.csv")
        projects = self._read("projects.csv")
        reviews = self._read("reviews.csv")
        history = self._read("employee_history.csv")

        conn = self.db.connect(settings.olap_db)
        try:
            cur = conn.cursor()
            if refresh:
                cur.execute("SET FOREIGN_KEY_CHECKS=0")
                for table in ["Fact_PerformanceReviews", "Dim_Employee", "Dim_Project", "Dim_Date", "Dim_Department"]:
                    cur.execute(f"TRUNCATE TABLE {table}")
                cur.execute("SET FOREIGN_KEY_CHECKS=1")

            # Dimensions.
            cur.executemany(
                "INSERT INTO Dim_Department(department_id,department_name,location,budget) VALUES (%s,%s,%s,%s)",
                list(departments[["department_id","department_name","location","budget"]].itertuples(index=False, name=None))
            )
            cur.executemany(
                "INSERT INTO Dim_Project(project_id,project_name,status,start_date,end_date) VALUES (%s,%s,%s,%s,%s)",
                list(projects[["project_id","project_name","status","start_date","end_date"]].itertuples(index=False, name=None))
            )

            # Date dimension based on review dates.
            dates = pd.date_range(pd.to_datetime(reviews["review_date"]).min(), pd.to_datetime(reviews["review_date"]).max(), freq="D")
            date_rows = []
            for dt in dates:
                date_rows.append((
                    int(dt.strftime("%Y%m%d")), dt.date(), int(dt.day), int(dt.month),
                    dt.strftime("%B"), int(dt.quarter), int(dt.year)
                ))
            cur.executemany("""INSERT INTO Dim_Date
                (date_sk,full_date,day_of_month,month_num,month_name,quarter_num,year_num)
                VALUES (%s,%s,%s,%s,%s,%s,%s)""", date_rows)

            dept_sk = {}
            cur.execute("SELECT department_id, department_sk FROM Dim_Department")
            for row in cur.fetchall(): dept_sk[row[0]] = row[1]
            project_sk = {}
            cur.execute("SELECT project_id, project_sk FROM Dim_Project")
            for row in cur.fetchall(): project_sk[row[0]] = row[1]

            # Historical versions first. The generated employee_history.csv
            # intentionally stores only the attributes that changed (department,
            # role, salary, and dates). Enrich each historical row from the
            # current employees.csv record before loading Dim_Employee.
            employee_lookup = (
                employees.set_index("employee_id")
                [["first_name", "last_name", "email", "gender", "age", "hire_date"]]
                .to_dict("index")
            )

            hist_rows = []
            for r in history.itertuples(index=False):
                base = employee_lookup[str(r.employee_id)]
                hist_rows.append((
                    r.employee_id,
                    base["first_name"],
                    base["last_name"],
                    base["email"],
                    base["gender"],
                    int(base["age"]),
                    dept_sk[int(r.department_id)],
                    r.role,
                    float(r.salary),
                    pd.Timestamp(base["hire_date"]).date(),
                    pd.Timestamp(r.start_date).date(),
                    pd.Timestamp(r.end_date).date(),
                    False,
                ))
            cur.executemany("""INSERT INTO Dim_Employee
                (employee_id,first_name,last_name,email,gender,age,department_sk,role,salary,hire_date,start_date,end_date,is_current)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", hist_rows)

            history_ids = set(history["employee_id"].astype(str))
            current_rows = []
            for r in employees.itertuples(index=False):
                start_date = pd.Timestamp("2025-01-01").date() if r.employee_id in history_ids else pd.Timestamp(r.hire_date).date()
                current_rows.append((r.employee_id,r.first_name,r.last_name,r.email,r.gender,int(r.age),dept_sk[int(r.department_id)],
                                     r.role,float(r.salary),pd.Timestamp(r.hire_date).date(),start_date,date(9999,12,31),True))
            cur.executemany("""INSERT INTO Dim_Employee
                (employee_id,first_name,last_name,email,gender,age,department_sk,role,salary,hire_date,start_date,end_date,is_current)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", current_rows)

            # Build the fact table by selecting the employee version valid at review date.
            # The SQL uses a CTE to demonstrate the requested transformation pattern.
            cur.execute("""INSERT INTO Fact_PerformanceReviews
                (review_id,employee_sk,project_sk,department_sk,date_sk,rating,review_score,review_count)
                WITH ranked_versions AS (
                    SELECT
                        r.review_id, r.employee_id, r.project_id, r.review_date,
                        r.rating, r.review_score,
                        e.employee_sk, e.department_sk,
                        ROW_NUMBER() OVER (
                            PARTITION BY r.review_id
                            ORDER BY e.start_date DESC
                        ) AS rn
                    FROM employee_oltp.Reviews r
                    JOIN Dim_Employee e
                      ON e.employee_id = r.employee_id
                     AND r.review_date BETWEEN e.start_date AND e.end_date
                )
                SELECT rv.review_id, rv.employee_sk, p.project_sk, rv.department_sk,
                       d.date_sk, rv.rating, rv.review_score, 1
                FROM ranked_versions rv
                JOIN Dim_Project p ON p.project_id=rv.project_id
                JOIN Dim_Date d ON d.full_date=rv.review_date
                WHERE rv.rn=1""")

            conn.commit()
            return {
                "departments": len(departments),
                "projects": len(projects),
                "dates": len(date_rows),
                "historical_versions": len(hist_rows),
                "current_versions": len(current_rows),
                "facts": len(reviews),
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
