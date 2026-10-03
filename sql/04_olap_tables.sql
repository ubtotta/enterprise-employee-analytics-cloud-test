USE employee_dw;

CREATE TABLE IF NOT EXISTS Dim_Department (
    department_sk INT AUTO_INCREMENT PRIMARY KEY,
    department_id INT NOT NULL,
    department_name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    budget DECIMAL(15,2),
    UNIQUE KEY uq_dim_department_natural (department_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Dim_Project (
    project_sk INT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(20) NOT NULL,
    project_name VARCHAR(160) NOT NULL,
    status VARCHAR(30),
    start_date DATE,
    end_date DATE,
    UNIQUE KEY uq_dim_project_natural (project_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Dim_Date (
    date_sk INT PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    day_of_month TINYINT NOT NULL,
    month_num TINYINT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    quarter_num TINYINT NOT NULL,
    year_num SMALLINT NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Dim_Employee (
    employee_sk BIGINT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(20) NOT NULL,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    email VARCHAR(160),
    gender VARCHAR(20),
    age INT,
    department_sk INT NOT NULL,
    role VARCHAR(120) NOT NULL,
    salary DECIMAL(15,2) NOT NULL,
    hire_date DATE NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    INDEX idx_dim_employee_natural (employee_id),
    INDEX idx_dim_employee_current (employee_id, is_current),
    INDEX idx_dim_employee_dates (start_date, end_date),
    CONSTRAINT fk_dim_employee_department FOREIGN KEY (department_sk) REFERENCES Dim_Department(department_sk)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Fact_PerformanceReviews (
    review_sk BIGINT AUTO_INCREMENT PRIMARY KEY,
    review_id VARCHAR(30) NOT NULL,
    employee_sk BIGINT NOT NULL,
    project_sk INT NOT NULL,
    department_sk INT NOT NULL,
    date_sk INT NOT NULL,
    rating TINYINT NOT NULL,
    review_score DECIMAL(6,2) NOT NULL,
    review_count INT NOT NULL DEFAULT 1,
    CONSTRAINT uq_fact_review UNIQUE (review_id),
    CONSTRAINT fk_fact_employee FOREIGN KEY (employee_sk) REFERENCES Dim_Employee(employee_sk),
    CONSTRAINT fk_fact_project FOREIGN KEY (project_sk) REFERENCES Dim_Project(project_sk),
    CONSTRAINT fk_fact_department FOREIGN KEY (department_sk) REFERENCES Dim_Department(department_sk),
    CONSTRAINT fk_fact_date FOREIGN KEY (date_sk) REFERENCES Dim_Date(date_sk),
    INDEX idx_fact_employee (employee_sk),
    INDEX idx_fact_project (project_sk),
    INDEX idx_fact_date (date_sk),
    INDEX idx_fact_department (department_sk)
) ENGINE=InnoDB;
