-- =====================================================================
-- Telco Churn Analysis | SQLite queries (run against data/telco.db)
-- Business question: Who is churning, why, and what is it costing us?
-- =====================================================================

-- Q1. Overall churn and monthly revenue at risk
SELECT COUNT(*)                                        AS customers,
       SUM(ChurnFlag)                                  AS churned,
       ROUND(100.0 * SUM(ChurnFlag) / COUNT(*), 2)     AS churn_rate_pct,
       ROUND(SUM(CASE WHEN ChurnFlag = 1 THEN MonthlyCharges END), 0) AS monthly_revenue_lost,
       ROUND(100.0 * SUM(CASE WHEN ChurnFlag = 1 THEN MonthlyCharges END) / SUM(MonthlyCharges), 2) AS pct_of_revenue_lost
FROM customers;

-- Q2. Churn by contract type
SELECT Contract,
       COUNT(*)                                    AS customers,
       ROUND(100.0 * AVG(ChurnFlag), 2)            AS churn_rate_pct
FROM customers
GROUP BY Contract
ORDER BY churn_rate_pct DESC;

-- Q3. Churn by tenure group (retention cliff)
SELECT TenureGroup,
       COUNT(*)                                    AS customers,
       ROUND(100.0 * AVG(ChurnFlag), 2)            AS churn_rate_pct
FROM customers
GROUP BY TenureGroup
ORDER BY MIN(tenure);

-- Q4. Segment cross-cut: contract x internet service
SELECT Contract, InternetService,
       COUNT(*) AS customers,
       ROUND(100.0 * AVG(ChurnFlag), 2) AS churn_rate_pct
FROM customers
GROUP BY Contract, InternetService
HAVING COUNT(*) >= 100
ORDER BY churn_rate_pct DESC;

-- Q5. Payment method and autopay effect
SELECT PaymentMethod,
       COUNT(*) AS customers,
       ROUND(100.0 * AVG(ChurnFlag), 2) AS churn_rate_pct
FROM customers
GROUP BY PaymentMethod
ORDER BY churn_rate_pct DESC;

-- Q6. Add-on services vs churn (CTE)
WITH addon_bucket AS (
    SELECT CASE WHEN InternetService = 'No' THEN 'No internet'
                WHEN AddOnCount = 0 THEN '0 add-ons'
                WHEN AddOnCount BETWEEN 1 AND 2 THEN '1-2 add-ons'
                ELSE '3+ add-ons' END AS addon_group,
           ChurnFlag
    FROM customers
)
SELECT addon_group, COUNT(*) AS customers,
       ROUND(100.0 * AVG(ChurnFlag), 2) AS churn_rate_pct
FROM addon_bucket
GROUP BY addon_group
ORDER BY churn_rate_pct DESC;

-- Q7. Retention by tenure year: share of customers in each tenure-year who did not churn
-- (tenure is months with the company, so this groups customers by how long they have stayed)
WITH cohorts AS (
    SELECT (tenure / 12) AS tenure_year, ChurnFlag
    FROM customers
)
SELECT tenure_year + 1 AS tenure_year,
       COUNT(*) AS customers,
       ROUND(100.0 * (1 - AVG(ChurnFlag)), 2) AS retained_pct
FROM cohorts
GROUP BY tenure_year
ORDER BY tenure_year;

-- Q8. Window function: rank segments by churned revenue
WITH seg AS (
    SELECT Contract || ' | ' || InternetService AS segment,
           COUNT(*) AS customers,
           SUM(ChurnFlag) AS churned,
           ROUND(SUM(CASE WHEN ChurnFlag = 1 THEN MonthlyCharges END), 0) AS revenue_lost
    FROM customers
    GROUP BY Contract, InternetService
)
SELECT segment, customers, churned, revenue_lost,
       ROUND(100.0 * revenue_lost / SUM(revenue_lost) OVER (), 2) AS pct_of_total_loss,
       ROUND(100.0 * SUM(revenue_lost) OVER (ORDER BY revenue_lost DESC) / SUM(revenue_lost) OVER (), 2) AS cumulative_pct,
       RANK() OVER (ORDER BY revenue_lost DESC) AS loss_rank
FROM seg
ORDER BY loss_rank;

-- Q9. Highest-risk target list: month-to-month, fiber, tenure <= 12, no autopay
SELECT customerID, tenure, MonthlyCharges, PaymentMethod
FROM customers
WHERE Contract = 'Month-to-month'
  AND InternetService = 'Fiber optic'
  AND tenure <= 12
  AND AutoPay = 'No'
  AND ChurnFlag = 0
ORDER BY MonthlyCharges DESC
LIMIT 50;
