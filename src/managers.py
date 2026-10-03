"""Data Access Layer and application services."""
from __future__ import annotations

from datetime import date
import uuid

import pandas as pd
from mysql.connector import Error

from config import settings
from src.db_manager import DatabaseConnection
from src.entities import Employee, Project, Review


class BaseManager:
    def __init__(self, database: str):
        self.database = database
        self.db = DatabaseConnection()

    def _connect(self):
        return self.db.connect(self.database)


class EmployeeManager(BaseManager):
    def __init__(self):
        super().__init__(settings.oltp_db)

    def list_employees(self, limit: int = 100):
        conn = None
        try:
            conn = self._connect()
            query = """SELECT e.employee_id, CONCAT(e.first_name, ' ', e.last_name) employee_name,
                       d.department_name, e.role, e.salary, e.status
                       FROM Employees e JOIN Departments d ON e.department_id=d.department_id
                       ORDER BY e.employee_id LIMIT %s"""
            return pd.read_sql(query, conn, params=(limit,))
        finally:
            if conn and conn.is_connected(): conn.close()

    def employee_exists(self, employee_id: str) -> bool:
        """Check whether an employee exists in the OLTP database."""

        conn = None

        try:
            conn = self._connect()

            cur = conn.cursor()

            cur.execute(
                """
                SELECT 1
                FROM Employees
                WHERE employee_id = %s
                LIMIT 1
                """,
                (employee_id,)
            )

            return cur.fetchone() is not None

        finally:
            if conn and conn.is_connected():
                conn.close()

    def get_departments(self):
        conn = None
        try:
            conn = self._connect()
            return pd.read_sql("SELECT department_id, department_name FROM Departments ORDER BY department_name", conn)
        finally:
            if conn and conn.is_connected(): conn.close()

    def add_employee(self, employee: Employee):
        """Validate and insert a new employee into the OLTP database."""

        # -----------------------------
        # Backend validation
        # -----------------------------

        if not employee.first_name.strip():
            raise ValueError("First name is required.")

        if not employee.last_name.strip():
            raise ValueError("Last name is required.")

        if not employee.email.strip():
            raise ValueError("Email is required.")

        # Age validation
        if not isinstance(employee.age, int):
            raise ValueError("Age must be an integer.")

        if employee.age < 18 or employee.age > 70:
            raise ValueError("Age must be between 18 and 70.")

        # Role validation
        role = employee.role.strip()

        if not role:
            raise ValueError("Role is required.")

        if role.isdigit():
            raise ValueError(
                "Role cannot contain only numbers."
            )

        if not any(char.isalpha() for char in role):
            raise ValueError(
                "Role must contain alphabetic characters."
            )

        # Salary validation
        if employee.salary <= 0:
            raise ValueError(
                "Salary must be greater than 0."
            )

        # Hire date validation
        if employee.hire_date > date.today():
            raise ValueError(
                "Hire date cannot be in the future."
            )

        conn = self._connect()

        try:
            cur = conn.cursor()

            cur.execute(
                """INSERT INTO Employees
                    (
                        employee_id,
                        first_name,
                        last_name,
                        email,
                        gender,
                        age,
                        department_id,
                        role,
                        salary,
                        hire_date,
                        status
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    employee.employee_id,
                    employee.first_name.strip(),
                    employee.last_name.strip(),
                    employee.email.strip(),
                    employee.gender,
                    employee.age,
                    employee.department_id,
                    role,
                    employee.salary,
                    employee.hire_date,
                    employee.status
                )
            )

            conn.commit()
            return True

        except Error:
            conn.rollback()
            raise

        finally:
            conn.close()

    def update_department_with_scd2(self, employee_id: str, new_department_id: int, effective_date: date):
        """Update OLTP department and maintain a Type-2 warehouse version."""
        conn_oltp = self._connect()
        conn_dw = self.db.connect(settings.olap_db)
        try:
            cur = conn_oltp.cursor(dictionary=True)
            cur.execute("SELECT * FROM Employees WHERE employee_id=%s", (employee_id,))
            employee = cur.fetchone()
            if not employee:
                raise ValueError(f"Employee {employee_id} was not found.")

            if int(employee["department_id"]) == int(new_department_id):
                return "Employee is already in that department."

            cur.execute("UPDATE Employees SET department_id=%s WHERE employee_id=%s", (new_department_id, employee_id))
            conn_oltp.commit()

            dw = conn_dw.cursor(dictionary=True)
            dw.execute("""SELECT employee_sk, department_sk FROM Dim_Employee
                         WHERE employee_id=%s AND is_current=TRUE ORDER BY employee_sk DESC LIMIT 1""", (employee_id,))
            current = dw.fetchone()
            dw.execute("SELECT department_sk FROM Dim_Department WHERE department_id=%s", (new_department_id,))
            new_dept = dw.fetchone()
            if not new_dept:
                raise ValueError("Target department is not present in the warehouse. Run ETL first.")

            if current:
                dw.execute("""UPDATE Dim_Employee SET end_date=%s, is_current=FALSE
                              WHERE employee_sk=%s AND is_current=TRUE""", (effective_date, current["employee_sk"]))
                start_date = effective_date
                dw.execute("""INSERT INTO Dim_Employee
                    (employee_id, first_name, last_name, email, gender, age, department_sk, role, salary, hire_date,
                     start_date, end_date, is_current)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'9999-12-31',TRUE)""",
                    (employee["employee_id"], employee["first_name"], employee["last_name"], employee["email"],
                     employee["gender"], employee["age"], new_dept["department_sk"], employee["role"],
                     employee["salary"], employee["hire_date"], start_date))
                conn_dw.commit()
            else:
                raise ValueError("No current warehouse employee version exists. Run ETL first.")
            return "Department updated in OLTP and a new SCD Type 2 warehouse version was created."
        except Exception:
            conn_oltp.rollback()
            conn_dw.rollback()
            raise
        finally:
            conn_oltp.close()
            conn_dw.close()


class ProjectManager(BaseManager):
    def __init__(self):
        super().__init__(settings.oltp_db)

    def add_project(self, project: Project):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("""INSERT INTO Projects(project_id, project_name, description, start_date, end_date, status)
                           VALUES (%s,%s,%s,%s,%s,%s)""",
                        (project.project_id, project.project_name, project.description,
                         project.start_date, project.end_date, project.status))
            conn.commit()
            return True
        except Error:
            conn.rollback(); raise
        finally:
            conn.close()

    def list_projects(self):
        conn = None
        try:
            conn = self._connect()
            return pd.read_sql("SELECT project_id, project_name, status, start_date, end_date FROM Projects ORDER BY project_name", conn)
        finally:
            if conn and conn.is_connected(): conn.close()

    def assign_employee(self, employee_id: str, project_id: str, role: str, start_date: date):
        conn = self._connect()
        try:
            cur = conn.cursor()
            assignment_id = f"A{uuid.uuid4().hex[:12].upper()}"
            cur.execute("""INSERT INTO Assignments
                (assignment_id, employee_id, project_id, assignment_role, start_date)
                VALUES (%s,%s,%s,%s,%s)""", (assignment_id, employee_id, project_id, role, start_date))
            conn.commit()
            return assignment_id
        except Error:
            conn.rollback(); raise
        finally:
            conn.close()


class ReviewManager(BaseManager):
    def __init__(self):
        super().__init__(settings.oltp_db)

    def add_review(self, review: Review):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("""INSERT INTO Reviews(review_id, employee_id, project_id, review_date, rating, review_score, comments)
                           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                        (review.review_id, review.employee_id, review.project_id, review.review_date,
                         review.rating, review.review_score, review.comments))
            conn.commit()
            return True
        except Error:
            conn.rollback(); raise
        finally:
            conn.close()


class AnalyticsManager(BaseManager):
    def __init__(self):
        super().__init__(settings.olap_db)

    def kpis(self):
        conn = None
        try:
            conn = self._connect()
            query = """SELECT
                (SELECT COUNT(DISTINCT employee_id) FROM Dim_Employee WHERE is_current=TRUE) AS employees,
                (SELECT COUNT(*) FROM Fact_PerformanceReviews) AS reviews,
                (SELECT ROUND(AVG(review_score),2) FROM Fact_PerformanceReviews) AS avg_score,
                (SELECT ROUND(SUM(review_score),2) FROM Fact_PerformanceReviews) AS total_score"""
            cur = conn.cursor(dictionary=True); cur.execute(query); return cur.fetchone()
        finally:
            if conn and conn.is_connected(): conn.close()

    def yearly_trend(self):
        conn = None
        try:
            conn = self._connect()
            return pd.read_sql("""SELECT d.year_num AS year, ROUND(AVG(f.review_score),2) avg_score
                                FROM Fact_PerformanceReviews f JOIN Dim_Date d ON d.date_sk=f.date_sk
                                GROUP BY d.year_num ORDER BY d.year_num""", conn)
        finally:
            if conn and conn.is_connected(): conn.close()

    def top_employees(self):
        conn = None
        try:
            conn = self._connect()
            query = """WITH scores AS (
                SELECT dd.department_name, de.employee_id,
                       CONCAT(de.first_name,' ',de.last_name) employee_name,
                       AVG(f.review_score) avg_score
                FROM Fact_PerformanceReviews f
                JOIN Dim_Employee de ON de.employee_sk=f.employee_sk
                JOIN Dim_Department dd ON dd.department_sk=f.department_sk
                GROUP BY dd.department_name,de.employee_id,de.first_name,de.last_name
            ), ranked AS (
                SELECT *, DENSE_RANK() OVER(PARTITION BY department_name ORDER BY avg_score DESC) performance_rank
                FROM scores
            ) SELECT * FROM ranked WHERE performance_rank <= 3
              ORDER BY department_name, performance_rank, employee_name"""
            return pd.read_sql(query, conn)
        finally:
            if conn and conn.is_connected(): conn.close()

    def project_bottlenecks(self):
        conn = None
        try:
            conn = self._connect()
            query = """SELECT p.project_name,
                       COUNT(DISTINCT f.employee_sk) employee_count,
                       COUNT(*) review_count,
                       ROUND(AVG(f.review_score),2) avg_score
                FROM Fact_PerformanceReviews f JOIN Dim_Project p ON p.project_sk=f.project_sk
                GROUP BY p.project_name ORDER BY employee_count DESC, review_count DESC"""
            return pd.read_sql(query, conn)
        finally:
            if conn and conn.is_connected(): conn.close()

    def department_performance(self):
        conn = None
        try:
            conn = self._connect()
            return pd.read_sql("""SELECT d.department_name,
                       COUNT(*) review_count, ROUND(AVG(f.review_score),2) avg_score
                       FROM Fact_PerformanceReviews f JOIN Dim_Department d ON d.department_sk=f.department_sk
                       GROUP BY d.department_name ORDER BY avg_score DESC""", conn)
        finally:
            if conn and conn.is_connected(): conn.close()
    def attrition_risk(self):
        """
        Analytical attrition-risk proxy derived from warehouse signals.

        This is NOT a trained predictive model.
        The numerical risk score is based on performance, tenure,
        and salary. Risk levels are assigned relative to the
        current employee population.
        """
        conn = None

        try:
            conn = self._connect()

            query = """
                WITH employee_scores AS (
                    SELECT
                        de.employee_id,

                        CONCAT(
                            de.first_name,
                            ' ',
                            de.last_name
                        ) AS employee_name,

                        de.salary,

                        TIMESTAMPDIFF(
                            YEAR,
                            de.hire_date,
                            CURDATE()
                        ) AS years_at_company,

                        AVG(f.review_score) AS avg_score

                    FROM Dim_Employee de

                    LEFT JOIN Fact_PerformanceReviews f
                        ON f.employee_sk = de.employee_sk

                    WHERE de.is_current = TRUE

                    GROUP BY
                        de.employee_id,
                        de.first_name,
                        de.last_name,
                        de.salary,
                        de.hire_date
                ),

                scored AS (
                    SELECT
                        *,
                        
                        ROUND(
                            LEAST(
                                100,
                                GREATEST(
                                    0,

                                    /* Performance component: 0-60 */
                                    GREATEST(
                                        0,
                                        (100 - COALESCE(avg_score, 70)) * 0.60
                                    )

                                    +

                                    /* Tenure component: 0-10 */
                                    CASE
                                        WHEN years_at_company BETWEEN 2 AND 5
                                            THEN 10
                                        WHEN years_at_company < 2
                                            THEN 8
                                        WHEN years_at_company BETWEEN 6 AND 10
                                            THEN 5
                                        ELSE 2
                                    END

                                    +

                                    /* Salary component: 0-15 */
                                    CASE
                                        WHEN salary < 300000
                                            THEN 15
                                        WHEN salary < 400000
                                            THEN 10
                                        WHEN salary < 500000
                                            THEN 5
                                        ELSE 0
                                    END

                                )
                            ),
                            2
                        ) AS risk_score

                    FROM employee_scores
                ),

                ranked AS (
                    SELECT
                        *,
                        
                        NTILE(20) OVER (
                            ORDER BY risk_score DESC
                        ) AS risk_group

                    FROM scored
                )

                SELECT
                    employee_id,
                    employee_name,
                    years_at_company,
                    ROUND(avg_score, 2) AS avg_score,
                    salary,
                    risk_score,

                    CASE
                        WHEN risk_group <= 4
                            THEN 'High'

                        WHEN risk_group <= 15
                            THEN 'Medium'

                        ELSE 'Low'
                    END AS risk_level

                FROM ranked

                ORDER BY
                    risk_score DESC,
                    employee_name
            """

            return pd.read_sql(query, conn)

        finally:
            if conn and conn.is_connected():
                conn.close()