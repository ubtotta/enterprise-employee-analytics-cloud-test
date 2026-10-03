USE employee_staging;

CREATE TABLE IF NOT EXISTS staging_employees (
    employee_id VARCHAR(20), first_name VARCHAR(80), last_name VARCHAR(80), email VARCHAR(160),
    gender VARCHAR(20), age INT, department_id INT, department_name VARCHAR(100), role VARCHAR(120),
    salary DECIMAL(15,2), hire_date DATE, status VARCHAR(30)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS staging_departments (
    department_id INT, department_name VARCHAR(100), location VARCHAR(100), budget DECIMAL(15,2)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS staging_projects (
    project_id VARCHAR(20), project_name VARCHAR(160), description VARCHAR(500),
    start_date DATE, end_date DATE, status VARCHAR(30)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS staging_assignments (
    assignment_id VARCHAR(30), employee_id VARCHAR(20), project_id VARCHAR(20), assignment_role VARCHAR(120),
    start_date DATE, end_date DATE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS staging_reviews (
    review_id VARCHAR(30), employee_id VARCHAR(20), project_id VARCHAR(20), review_date DATE,
    rating TINYINT, review_score DECIMAL(6,2), comments VARCHAR(1000)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS staging_employee_history (
    employee_id VARCHAR(20), department_id INT, department_name VARCHAR(100), role VARCHAR(120),
    salary DECIMAL(15,2), start_date DATE, end_date DATE, is_current BOOLEAN
) ENGINE=InnoDB;
