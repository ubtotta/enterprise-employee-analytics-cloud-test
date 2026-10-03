USE employee_dw;

-- 1. Year-over-year performance trend.
SELECT d.year_num, ROUND(AVG(f.review_score), 2) AS avg_score
FROM Fact_PerformanceReviews f
JOIN Dim_Date d ON d.date_sk = f.date_sk
GROUP BY d.year_num
ORDER BY d.year_num;

-- 2. Top-performing employees per department using DENSE_RANK().
WITH employee_scores AS (
    SELECT
        de.department_sk,
        dd.department_name,
        de.employee_id,
        CONCAT(de.first_name, ' ', de.last_name) AS employee_name,
        AVG(f.review_score) AS avg_score
    FROM Fact_PerformanceReviews f
    JOIN Dim_Employee de ON de.employee_sk = f.employee_sk
    JOIN Dim_Department dd ON dd.department_sk = f.department_sk
    GROUP BY de.department_sk, dd.department_name, de.employee_id,
             de.first_name, de.last_name
), ranked AS (
    SELECT *, DENSE_RANK() OVER (
        PARTITION BY department_sk ORDER BY avg_score DESC
    ) AS performance_rank
    FROM employee_scores
)
SELECT * FROM ranked
WHERE performance_rank <= 3
ORDER BY department_name, performance_rank;

-- 3. Project bottleneck analysis.
SELECT
    p.project_id,
    p.project_name,
    COUNT(DISTINCT f.employee_sk) AS employees_reviewed,
    COUNT(*) AS review_count,
    ROUND(AVG(f.review_score), 2) AS avg_score
FROM Fact_PerformanceReviews f
JOIN Dim_Project p ON p.project_sk = f.project_sk
GROUP BY p.project_id, p.project_name
ORDER BY employees_reviewed DESC, review_count DESC;
