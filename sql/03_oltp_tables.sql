USE employee_oltp;

CREATE TABLE IF NOT EXISTS Departments (
    department_id INT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    location VARCHAR(100) NOT NULL,
    budget DECIMAL(15,2) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Employees (
    employee_id VARCHAR(20) PRIMARY KEY,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    email VARCHAR(160) NOT NULL UNIQUE,
    gender VARCHAR(20),
    age INT,
    department_id INT NOT NULL,
    role VARCHAR(120) NOT NULL,
    salary DECIMAL(15,2) NOT NULL,
    hire_date DATE NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_employee_department FOREIGN KEY (department_id) REFERENCES Departments(department_id),
    INDEX idx_employee_department (department_id),
    INDEX idx_employee_status (status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Projects (
    project_id VARCHAR(20) PRIMARY KEY,
    project_name VARCHAR(160) NOT NULL,
    description VARCHAR(500),
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(30) NOT NULL,
    INDEX idx_project_status (status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Assignments (
    assignment_id VARCHAR(30) PRIMARY KEY,
    employee_id VARCHAR(20) NOT NULL,
    project_id VARCHAR(20) NOT NULL,
    assignment_role VARCHAR(120) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    CONSTRAINT fk_assignment_employee FOREIGN KEY (employee_id) REFERENCES Employees(employee_id),
    CONSTRAINT fk_assignment_project FOREIGN KEY (project_id) REFERENCES Projects(project_id),
    INDEX idx_assignment_employee (employee_id),
    INDEX idx_assignment_project (project_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Reviews (
    review_id VARCHAR(30) PRIMARY KEY,
    employee_id VARCHAR(20) NOT NULL,
    project_id VARCHAR(20) NOT NULL,
    review_date DATE NOT NULL,
    rating TINYINT NOT NULL,
    review_score DECIMAL(6,2) NOT NULL,
    comments VARCHAR(1000),
    CONSTRAINT chk_review_rating CHECK (rating BETWEEN 1 AND 5),
    CONSTRAINT fk_review_employee FOREIGN KEY (employee_id) REFERENCES Employees(employee_id),
    CONSTRAINT fk_review_project FOREIGN KEY (project_id) REFERENCES Projects(project_id),
    INDEX idx_review_employee_date (employee_id, review_date),
    INDEX idx_review_project (project_id)
) ENGINE=InnoDB;
