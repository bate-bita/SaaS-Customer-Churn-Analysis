-- ============================================================
-- PulseHQ SaaS Customer Churn Analysis
-- SQL Queries | DB Browser for SQLite
-- Author: Bate Bita Tambe
-- ============================================================


-- ============================================================
-- Query 1: Monthly Churn Trend
-- Business Purpose: Track how many customers churned each month
-- to identify peak churn periods and seasonal patterns.
-- ============================================================

SELECT
    strftime('%Y-%m', churn_date)    AS churn_month,
    COUNT(*)                         AS churned_customers
FROM customers
WHERE churned = 1
GROUP BY churn_month
ORDER BY churn_month;


-- ============================================================
-- Query 2: Churn Rate by Subscription Plan
-- Business Purpose: Identify which subscription plan has the
-- highest churn risk and quantify the revenue exposure per plan.
-- ============================================================

SELECT
    subscription_plan,
    COUNT(*)                                           AS total_customers,
    SUM(churned)                                       AS churned_customers,
    ROUND(SUM(churned) * 100.0 / COUNT(*), 2)          AS churn_rate_pct,
    ROUND(SUM(CASE WHEN churned = 1
              THEN monthly_recurring_revenue ELSE 0
              END), 2)                                 AS total_mrr_lost
FROM customers
GROUP BY subscription_plan
ORDER BY churn_rate_pct DESC;


-- ============================================================
-- Query 3: Churned MRR by Customer Segment
-- Business Purpose: Understand which customer segment causes
-- the most financial damage when they leave PulseHQ.
-- ============================================================

SELECT
    company_size,
    COUNT(*)                                           AS churned_customers,
    ROUND(SUM(monthly_recurring_revenue), 2)           AS total_mrr_lost,
    ROUND(AVG(monthly_recurring_revenue), 2)           AS avg_mrr_lost
FROM customers
WHERE churned = 1
GROUP BY company_size
ORDER BY total_mrr_lost DESC;


-- ============================================================
-- Query 4: High Churn Risk Customers (CTE)
-- Business Purpose: Flag currently active customers showing
-- the same warning signs as customers who already churned.
-- Enables the retention team to intervene proactively.
-- ============================================================

WITH churn_signals AS (
    SELECT
        customer_id,
        company_name,
        subscription_plan,
        contract_type,
        monthly_recurring_revenue,
        support_tickets_raised,
        nps_score,
        last_login_days_ago,
        tenure_months,
        (CASE WHEN support_tickets_raised >= 5 THEN 2 ELSE 0 END +
         CASE WHEN nps_score <= 5             THEN 2 ELSE 0 END +
         CASE WHEN last_login_days_ago >= 20  THEN 1 ELSE 0 END +
         CASE WHEN tenure_months <= 3         THEN 1 ELSE 0 END +
         CASE WHEN contract_type = 'Monthly'  THEN 1 ELSE 0 END
        )                                              AS risk_score
    FROM customers
    WHERE churned = 0
)
SELECT
    customer_id,
    company_name,
    subscription_plan,
    contract_type,
    monthly_recurring_revenue,
    nps_score,
    support_tickets_raised,
    risk_score,
    CASE
        WHEN risk_score >= 5 THEN 'High Risk'
        WHEN risk_score >= 3 THEN 'Medium Risk'
        ELSE 'Low Risk'
    END                                                AS risk_category
FROM churn_signals
WHERE risk_score >= 3
ORDER BY risk_score DESC, monthly_recurring_revenue DESC;


-- ============================================================
-- Query 5: Top Customers by MRR Using RANK()
-- Business Purpose: Identify the highest revenue customers
-- so the retention team knows exactly who to prioritize
-- before they churn.
-- ============================================================

SELECT
    customer_id,
    company_name,
    subscription_plan,
    company_size,
    monthly_recurring_revenue,
    contract_type,
    churned,
    RANK() OVER (
        ORDER BY monthly_recurring_revenue DESC
    )                                                  AS revenue_rank
FROM customers
ORDER BY revenue_rank
LIMIT 20;