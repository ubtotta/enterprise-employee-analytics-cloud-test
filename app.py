from __future__ import annotations

from datetime import date, timedelta
import uuid
import re

import streamlit as st
import plotly.express as px

from src.db_manager import DatabaseConnection
from src.entities import Employee, Project, Review
from src.managers import EmployeeManager, ProjectManager, ReviewManager, AnalyticsManager
from config import settings

from pathlib import Path
from src.etl import EmployeeWarehouseETL

st.set_page_config(page_title="Enterprise Employee Analytics", page_icon="📊", layout="wide")


def manager_error(fn):
    try:
        return fn()
    except Exception as exc:
        st.error(f"Operation failed: {exc}")
        return None


def sidebar():
    st.sidebar.title("Enterprise HR Analytics")
    st.sidebar.caption("OLTP + ETL + OLAP + SCD Type 2")
    return st.sidebar.radio("Navigate", ["Dashboard", "Employee Management", "Projects", "Performance Reviews", "System Info"])


def dashboard():
    st.title("📊 Executive Analytics Dashboard")
    st.write("Analytics are read directly from the MySQL Star Schema warehouse.")

    if st.button("🔄 Refresh Warehouse", type="primary"):
        try:
            with st.spinner("Refreshing warehouse from OLTP..."):

                etl = EmployeeWarehouseETL(
                    Path("data/generated")
                )

                result = etl.refresh_from_oltp()

            st.session_state["warehouse_refresh_result"] = result
            st.session_state["warehouse_refresh_success"] = True

            st.rerun()

        except Exception as exc:
            st.session_state["warehouse_refresh_error"] = str(exc)
            st.rerun()

    # Show the result after Streamlit reruns
    if st.session_state.get("warehouse_refresh_success"):
        result = st.session_state["warehouse_refresh_result"]

        st.success("✅ Warehouse refreshed successfully.")

        st.write("**Refresh Summary**")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Departments",
            result["departments_synced"]
        )

        col2.metric(
            "Projects",
            result["projects_synced"]
        )

        col3.metric(
            "New Employees",
            result["new_employees"]
        )

        col4.metric(
            "Reviews Synchronized",
            result["reviews_processed"]
        )

    if st.session_state.get("warehouse_refresh_error"):
        st.error(
            "❌ Warehouse refresh failed: "
            + st.session_state["warehouse_refresh_error"]
        )


    analytics = AnalyticsManager()
    kpi = manager_error(analytics.kpis)
    if not kpi:
        st.info("Load the OLTP data and run ETL before opening analytics.")
        return
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current Employees", f"{kpi['employees'] or 0:,}")
    c2.metric("Performance Reviews", f"{kpi['reviews'] or 0:,}")
    c3.metric("Average Score", f"{float(kpi['avg_score'] or 0):.2f}")
    c4.metric("Total Review Score", f"{float(kpi['total_score'] or 0):,.0f}")

    trend = manager_error(analytics.yearly_trend)
    if trend is not None and not trend.empty:
        st.subheader("Year-over-Year Performance Trend")
        fig = px.line(
        trend,
        x="year",
        y="avg_score",
        markers=True,
        title="Average Performance Score by Year"
    )

    fig.update_traces(
        line=dict(color="#38BDF8", width=3),
        marker=dict(size=8)
    )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E5E7EB"),
        title_font=dict(size=18),
        xaxis=dict(
            title="Year",
            gridcolor="#374151"
        ),
        yaxis=dict(
            title="Average Score",
            gridcolor="#374151"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Top Employees by Department")
        top = manager_error(analytics.top_employees)
        if top is not None:
            st.dataframe(top, use_container_width=True, hide_index=True)
    with right:
        st.subheader("Project Bottleneck / Workload")
        projects = manager_error(analytics.project_bottlenecks)
        if projects is not None and not projects.empty:
            fig = px.bar(
            projects,
            x="project_name",
            y="employee_count",
            title="Employees Reviewed per Project",
            color="project_name",
            color_discrete_sequence=[
                "#06B6D4",
                "#6366F1",
                "#8B5CF6",
                "#EC4899",
                "#F59E0B",
                "#14B8A6",
                "#22C55E",
                "#3B82F6",
                "#F97316",
                "#A855F7"
            ]
        )

        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E5E7EB"),
            title_font=dict(size=18),
            showlegend=False,
            margin=dict(l=40, r=20, t=60, b=80),
            xaxis=dict(
                title="Project",
                gridcolor="#374151",
                tickangle=-35
            ),
            yaxis=dict(
                title="Employees Reviewed",
                gridcolor="#374151"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.subheader("Department Performance")
    dept = manager_error(analytics.department_performance)
    if dept is not None and not dept.empty:
        fig = px.bar(
        dept,
        x="department_name",
        y="avg_score",
        title="Average Review Score by Department",
        color="department_name",
        color_discrete_map={
            "Engineering": "#6366F1",
            "Marketing": "#EC4899",
            "Human Resources": "#14B8A6",
            "Finance": "#F59E0B",
            "Operations": "#8B5CF6",
            "Sales": "#06B6D4"
        }
    )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E5E7EB"),
        title_font=dict(size=18),
        showlegend=False,
        margin=dict(l=40, r=20, t=60, b=40),
        xaxis=dict(
            title="Department",
            gridcolor="#374151"
        ),
        yaxis=dict(
            title="Average Review Score",
            gridcolor="#374151"
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


    st.subheader("Employee Attrition Risk — Analytical Proxy")
    st.caption("Transparent warehouse-derived risk indicator for demonstration; this is not a trained predictive model.")
    risk = manager_error(analytics.attrition_risk)
    if risk is not None and not risk.empty:

        rc1, rc2 = st.columns([1.15, 1])

        with rc1:

            counts = (
                risk["risk_level"]
                .value_counts()
                .reindex(["High", "Medium", "Low"])
                .fillna(0)
                .reset_index()
            )

            counts.columns = ["risk_level", "employee_count"]

            fig = px.bar(
                counts,
                x="risk_level",
                y="employee_count",
                title="Employees by Risk Level",
                color="risk_level",
                color_discrete_map={
                    "High": "#EF4444",
                    "Medium": "#F59E0B",
                    "Low": "#22C55E"
                }
            )

            fig.update_layout(
                height=450,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E5E7EB"),
                title_font=dict(size=18),
                showlegend=False,
                margin=dict(l=40, r=20, t=60, b=40),
                xaxis=dict(
                    title="Risk Level",
                    gridcolor="#374151"
                ),
                yaxis=dict(
                    title="Employee Count",
                    gridcolor="#374151"
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        with rc2:

            st.dataframe(
                risk.head(15),
                use_container_width=True,
                hide_index=True,
                height=450
            )


def validate_employee_input(first, last, email, age, role, salary, hire_date):
    """
    Validate employee input before creating the Employee object.
    Returns:
        None  -> valid
        str   -> validation error message
    """

    # Name validation
    if not first.strip():
        return "First name is required."

    if not last.strip():
        return "Last name is required."

    if not re.fullmatch(r"[A-Za-z][A-Za-z\s'-]*", first.strip()):
        return "First name can contain only letters, spaces, apostrophes and hyphens."

    if not re.fullmatch(r"[A-Za-z][A-Za-z\s'-]*", last.strip()):
        return "Last name can contain only letters, spaces, apostrophes and hyphens."

    # Email validation
    email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    if not re.fullmatch(email_pattern, email.strip()):
        return "Please enter a valid email address."

    # Age validation
    try:
        age = int(age)
    except (TypeError, ValueError):
        return "Age must be a valid number."

    if age < 18 or age > 70:
        return "Age must be between 18 and 70."

    # Role validation
    role = role.strip()

    if not role:
        return "Role is required."

    # Reject purely numeric roles such as 12345
    if role.isdigit():
        return "Role cannot contain only numbers. Please enter a valid job role."

    # Require at least one alphabetic character
    if not re.search(r"[A-Za-z]", role):
        return "Role must contain alphabetic characters."

    # Salary validation
    try:
        salary = float(salary)
    except (TypeError, ValueError):
        return "Salary must be a valid number."

    if salary <= 0:
        return "Salary must be greater than 0."

    # Hire date validation
    if hire_date > date.today():
        return "Hire date cannot be in the future."

    return None

def employee_management():
    st.title("👥 Employee Management")
    manager = EmployeeManager()
    departments = manager_error(manager.get_departments)
    if departments is None or departments.empty:
        st.warning("No departments found. Create the database and run the data loader first.")
        return

    tab1, tab2, tab3 = st.tabs(["Onboard Employee", "Change Department (SCD2)", "View Employees"])

    with tab1:
        with st.form("employee_onboard_form", clear_on_submit=False):
            col1, col2 = st.columns(2)

            first = col1.text_input("First name")
            last = col2.text_input("Last name")

            email = col1.text_input("Email")

            gender = col2.selectbox(
                "Gender",
                ["Male", "Female", "Other"]
            )

            # We validate this ourselves after submission
            age = col1.number_input(
                "Age",
                value=28,
                step=1
            )

            role = col2.text_input(
                "Role",
                value="Software Engineer"
            )

            salary = col1.number_input(
                "Annual Salary",
                value=800000.0,
                step=25000.0
            )

            dept = col2.selectbox(
                "Department",
                departments["department_name"].tolist()
            )

            hire_date = col1.date_input(
                "Hire date",
                value=date.today()
            )

            submitted = st.form_submit_button(
                "Onboard Employee"
            )

        # IMPORTANT:
        # Keep submission handling OUTSIDE the st.form block.
        if submitted:

            validation_error = validate_employee_input(
                first=first,
                last=last,
                email=email,
                age=age,
                role=role,
                salary=salary,
                hire_date=hire_date
            )

            # INVALID DATA
            if validation_error:
                st.error(validation_error)

            # VALID DATA ONLY
            else:
                dept_id = int(
                    departments.loc[
                        departments["department_name"] == dept,
                        "department_id"
                    ].iloc[0]
                )

                employee = Employee(
                    employee_id=f"E{uuid.uuid4().hex[:8].upper()}",
                    first_name=first.strip(),
                    last_name=last.strip(),
                    email=email.strip(),
                    gender=gender,
                    age=int(age),
                    department_id=dept_id,
                    role=role.strip(),
                    salary=float(salary),
                    hire_date=hire_date
                )

                try:
                    manager.add_employee(employee)

                    st.success(
                        f"Employee {employee.employee_id} "
                        f"onboarded successfully."
                    )

                except Exception as exc:
                    st.error(
                        f"Employee could not be onboarded: {exc}"
                    )

    with tab2:
        st.caption(
            "This operation updates the normalized OLTP employee and creates "
            "a new current warehouse version while closing the previous version."
        )

        emp_id = st.text_input(
            "Employee ID",
            placeholder="Example: TEST_REFRESH_001"
        ).strip().upper()

        new_dept = st.selectbox(
            "New Department",
            departments["department_name"].tolist(),
            key="newdept"
        )

        effective = st.date_input(
            "Effective date",
            value=date.today(),
            key="effective"
        )

        if st.button("Apply Department Change"):

            if not emp_id:
                st.error("Please enter an Employee ID.")
            else:
                # Verify that the employee exists in OLTP
                exists = manager_error(
                    lambda: manager.employee_exists(emp_id)
                )

                if exists is None:
                    st.error("Unable to verify the Employee ID.")
                elif not exists:
                    st.error(
                        f"Employee ID '{emp_id}' was not found in the OLTP database."
                    )
                else:
                    dept_id = int(
                        departments.loc[
                            departments.department_name == new_dept,
                            "department_id"
                        ].iloc[0]
                    )

                    msg = manager_error(
                        lambda: manager.update_department_with_scd2(
                            emp_id,
                            dept_id,
                            effective
                        )
                    )

                    if msg:
                        st.success(msg)

    with tab3:
        employee_df = manager_error(lambda: manager.list_employees(500))
        if employee_df is not None:
            st.dataframe(employee_df, use_container_width=True, hide_index=True)


def projects_page():
    st.title("📁 Project Management")
    manager = ProjectManager()
    tab1, tab2 = st.tabs(["Create Project", "Assignments"])
    with tab1:
        with st.form("project_form"):
            name = st.text_input("Project name")
            desc = st.text_area("Description")
            start = st.date_input("Start date", value=date.today())
            end = st.date_input("End date", value=date.today() + timedelta(days=180))
            status = st.selectbox("Status", ["Planned", "Active", "Completed"])
            if st.form_submit_button("Create Project"):
                if not name.strip():
                    st.error("Project name is required.")
                else:
                    project = Project(f"P{uuid.uuid4().hex[:8].upper()}", name.strip(), desc.strip(), start, end, status)
                    if manager_error(lambda: manager.add_project(project)) is not None:
                        st.success(f"Project {project.project_id} created.")
    with tab2:
        em = EmployeeManager()

        projects = manager_error(manager.list_projects)

        if projects is None or projects.empty:
            st.warning("Projects are required before creating assignments.")
        else:
            employee_id = st.text_input(
                "Employee ID",
                placeholder="Example: TEST_REFRESH_001"
            ).strip().upper()

            project_id = st.selectbox(
                "Project",
                projects.project_id.tolist()
            )

            role = st.text_input(
                "Assignment role",
                value="Team Member"
            )

            start = st.date_input(
                "Assignment start",
                value=date.today(),
                key="assignment_start"
            )

            if st.button("Assign Employee"):

                if not employee_id:
                    st.error("Please enter an Employee ID.")

                elif not role.strip():
                    st.error("Assignment role is required.")

                else:
                    employee_exists = manager_error(
                        lambda: em.employee_exists(employee_id)
                    )

                    if employee_exists is None:
                        st.error("Unable to verify the Employee ID.")

                    elif not employee_exists:
                        st.error(
                            f"Employee ID '{employee_id}' "
                            "was not found in the OLTP database."
                        )

                    else:
                        result = manager_error(
                            lambda: manager.assign_employee(
                                employee_id,
                                project_id,
                                role.strip(),
                                start
                            )
                        )

                        if result:
                            st.success(
                                f"Assignment {result} created for "
                                f"employee {employee_id}."
                            )


def reviews_page():
    st.title("⭐ Performance Reviews")

    em = EmployeeManager()
    pm = ProjectManager()
    rm = ReviewManager()

    projects = manager_error(pm.list_projects)

    if projects is None or projects.empty:
        st.warning("Projects are required before submitting reviews.")
        return

    # Employee ID is entered directly so the application can support
    # 100K+ employees without loading all employees into a dropdown.
    employee_id = st.text_input(
        "Employee ID",
        placeholder="Example: TEST_REFRESH_001"
    ).strip().upper()

    project_id = st.selectbox(
        "Project",
        projects.project_id.tolist()
    )

    review_date = st.date_input(
        "Review date",
        value=date.today()
    )

    rating = st.slider(
        "Rating",
        1,
        5,
        4
    )

    score = st.slider(
        "Performance score",
        0.0,
        100.0,
        80.0,
        0.5
    )

    comments = st.text_area(
        "Comments",
        value="Quarterly performance review"
    )

    if st.button("Submit Review"):

        # ---------------------------------------------------------
        # Validate Employee ID
        # ---------------------------------------------------------
        if not employee_id:
            st.error("Please enter an Employee ID.")

        else:
            employee_exists = manager_error(
                lambda: em.employee_exists(employee_id)
            )

            if employee_exists is None:
                st.error("Unable to verify the Employee ID.")

            elif not employee_exists:
                st.error(
                    f"Employee ID '{employee_id}' "
                    "was not found in the OLTP database."
                )

            else:
                # -------------------------------------------------
                # Create review
                # -------------------------------------------------
                review = Review(
                    f"R{uuid.uuid4().hex[:10].upper()}",
                    employee_id,
                    project_id,
                    review_date,
                    int(rating),
                    float(score),
                    comments.strip()
                )

                result = manager_error(
                    lambda: rm.add_review(review)
                )

                if result is not None:
                    st.success(
                        f"Review {review.review_id} "
                        f"saved to OLTP for employee {employee_id}."
                    )
                    st.info(
                        "Click 'Refresh Warehouse' from the Dashboard "
                        "to load this review into OLAP analytics."
                    )


def system_info():
    st.title("⚙️ System Information")
    st.code(f"OLTP: {settings.host}:{settings.port}/{settings.oltp_db}\nOLAP: {settings.host}:{settings.port}/{settings.olap_db}")
    ok, message = DatabaseConnection().test_connection(settings.oltp_db)
    if ok: st.success(message)
    else: st.error(message)
    st.markdown("### Pipeline")
    st.markdown("`Python/Faker → CSV → MySQL OLTP → ETL/CTEs/Window Functions/SCD2 → MySQL OLAP → Streamlit/Plotly`")
    st.markdown("### Team modules")
    st.markdown("- **Person 1:** Data synthesis + OLTP\n- **Person 2:** OLAP + ETL + SQL\n- **Person 3:** OOP + Streamlit + Analytics")


page = sidebar()
if page == "Dashboard": dashboard()
elif page == "Employee Management": employee_management()
elif page == "Projects": projects_page()
elif page == "Performance Reviews": reviews_page()
else: system_info()
