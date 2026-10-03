USE employee_dw;

DROP PROCEDURE IF EXISTS sp_upsert_department;
DROP PROCEDURE IF EXISTS sp_load_project;
DROP PROCEDURE IF EXISTS sp_load_review_fact;

DELIMITER $$

CREATE PROCEDURE sp_upsert_department(
    IN p_department_id INT,
    IN p_department_name VARCHAR(100),
    IN p_location VARCHAR(100),
    IN p_budget DECIMAL(15,2)
)
BEGIN
    INSERT INTO Dim_Department(department_id, department_name, location, budget)
    VALUES(p_department_id, p_department_name, p_location, p_budget)
    ON DUPLICATE KEY UPDATE
        department_name = VALUES(department_name),
        location = VALUES(location),
        budget = VALUES(budget);
END$$

CREATE PROCEDURE sp_load_project(
    IN p_project_id VARCHAR(20),
    IN p_project_name VARCHAR(160),
    IN p_status VARCHAR(30),
    IN p_start_date DATE,
    IN p_end_date DATE
)
BEGIN
    INSERT INTO Dim_Project(project_id, project_name, status, start_date, end_date)
    VALUES(p_project_id, p_project_name, p_status, p_start_date, p_end_date)
    ON DUPLICATE KEY UPDATE
        project_name = VALUES(project_name),
        status = VALUES(status),
        start_date = VALUES(start_date),
        end_date = VALUES(end_date);
END$$

CREATE PROCEDURE sp_load_review_fact(IN p_review_id VARCHAR(30))
BEGIN
    INSERT INTO Fact_PerformanceReviews(
        review_id, employee_sk, project_sk, department_sk, date_sk,
        rating, review_score, review_count
    )
    SELECT
        r.review_id,
        e.employee_sk,
        p.project_sk,
        e.department_sk,
        d.date_sk,
        r.rating,
        r.review_score,
        1
    FROM employee_oltp.Reviews r
    JOIN Dim_Employee e
      ON e.employee_id = r.employee_id
     AND r.review_date BETWEEN e.start_date AND e.end_date
    JOIN Dim_Project p ON p.project_id = r.project_id
    JOIN Dim_Date d ON d.full_date = r.review_date
    WHERE r.review_id = p_review_id
    ON DUPLICATE KEY UPDATE
        employee_sk = VALUES(employee_sk),
        project_sk = VALUES(project_sk),
        department_sk = VALUES(department_sk),
        date_sk = VALUES(date_sk),
        rating = VALUES(rating),
        review_score = VALUES(review_score);
END$$

DELIMITER ;
