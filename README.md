# SaaS Customer Churn Analysis | SQL + Power BI

A two-layer analytical project combining SQL data querying and Power BI dashboard visualization to analyze customer churn for **PulseHQ**, a fictional B2B CRM SaaS platform. The project answers a single core business question: which customers are churning, what are the key drivers, and how much recurring revenue is at risk?

---

## Project Overview

**Company:** PulseHQ, a fictional B2B CRM SaaS platform serving Small, Mid-Market, and Enterprise customers across Basic, Professional, and Enterprise subscription plans.

**Business Problem:** PulseHQ is experiencing an overall churn rate of 35.4%, with monthly contract customers churning at nearly 4x the rate of annual customers. Leadership needs visibility into churn patterns, revenue impact, and at-risk customers to inform retention strategy.

**Analytical Approach:** The project is structured in two layers. The SQL layer extracts and aggregates raw customer data to surface churn patterns and revenue exposure. The Power BI layer translates those findings into an interactive 3-page executive dashboard for business stakeholders.

---

## Dataset

The dataset was generated in Python using realistic business logic and narrative patterns designed to tell a compelling and coherent churn story.

**Scope:** 500 customers, 12 months (January to December 2024)

**Tables:**
- `customers` — one row per customer with subscription, behavioral, and churn attributes
- `monthly_mrr` — one row per month with aggregated MRR and churn metrics

**Key fields:** customer_id, company_name, company_size, subscription_plan, contract_type, monthly_recurring_revenue, signup_date, churn_date, churned, tenure_months, support_tickets_raised, nps_score, last_login_days_ago, cohort_month

**Narrative patterns engineered into the data:**
- Basic plan customers churn at 57% vs Enterprise at only 11%
- Monthly contract customers churn at nearly 4x the rate of annual customers
- Q3 (July to September) is the peak churn period with July recording the highest single-month churn
- Churned customers average an NPS score of 3.24 vs 6.98 for active customers
- Churned customers raise an average of 5.62 support tickets vs 2.12 for active customers
- Short tenure customers (under 3 months) churn disproportionately, signaling an onboarding problem

---

## SQL Analysis

**Tool:** SQLite via DB Browser for SQLite

**File:** `sql/pulsehq_queries.sql`

### Query 1: Monthly Churn Trend
Tracks how many customers churned each month to identify peak churn periods and seasonal patterns.

![Query 1 Results](Query%20Results/Monthly%20Churn%20Trend.png)

### Query 2: Churn Rate by Subscription Plan
Identifies which subscription plan carries the highest churn risk and quantifies revenue exposure per plan.

![Query 2 Results](Query%20Results/Churn%20Rate%20by%20Subscription%20Plan.png)

### Query 3: Churned MRR by Customer Segment
Breaks down total and average MRR lost by company size to identify which segment causes the most financial damage when customers leave.

![Query 3 Results](Query%20Results/Churned%20MRR%20by%20Customer%20Segment.png)

### Query 4: High Churn Risk Customers (CTE)
Uses a Common Table Expression to build a behavioral risk scoring model that flags currently active customers showing the same warning signs as customers who already churned. Risk scores are based on five signals: high support ticket volume, low NPS score, recent login inactivity, short tenure, and monthly contract type. Outputs a prioritized retention action list.

![Query 4 Results Part 1](Query%20Results/High%20Churn%20Risk%20Customers%20(CTE)%20-%201.png)
![Query 4 Results Part 2](Query%20Results/High%20Churn%20Risk%20Customers%20(CTE)%20-%202.png)

### Query 5: Top Customers by MRR Using RANK()
Uses a window function to rank all customers by monthly recurring revenue, identifying the highest-value accounts the retention team should prioritize before they churn.

![Query 5 Results](Query%20Results/Top%20Customers%20by%20MRR%20Using%20RANK().png)

---

## Power BI Dashboard

**Tool:** Power BI Desktop

**Pages:** 3

**Data model:** Star-schema style relationship between `customers` and `monthly_mrr` tables joined on cohort month, with 10 custom DAX measures.

### Page 1: Churn Overview
High-level summary of churn volume, rate, and revenue split. Includes monthly churn trend, churn rate by subscription plan, churn rate by contract type, and a revenue split donut chart showing active vs churned MRR.

![Page 1](Power%20BI%20Screenshots/Churn%20Overview.png)

### Page 2: Revenue Impact
Financial deep-dive into MRR loss. Includes total MRR, churned MRR, and active customer KPIs, a monthly MRR loss column chart, churned MRR by customer segment, a monthly MRR loss waterfall chart, and a top 10 churned customers table ranked by revenue.

![Page 2](Power%20BI%20Screenshots/Revenue%20Impact.png)

### Page 3: Customer Segment Analysis
Segment-level breakdown of churn behavior. Includes NPS comparison between churned and active customers, churn rate by company size, churn rate by contract type, customer distribution by segment, and average support tickets for churned vs active customers.

![Page 3](Power%20BI%20Screenshots/Customer%20Segment%20Analysis.png)

---

## Key Business Insights

- PulseHQ's overall churn rate stands at **35.4%**, with 177 of 500 customers lost and **$82.56K in MRR** at risk
- Basic plan customers churn at **57%** while Enterprise customers churn at only **11%**, a 5x difference driven primarily by product fit and contract commitment
- Monthly contract customers churn at **52%** versus **13%** for annual customers, suggesting that converting customers to annual contracts during onboarding is a critical retention lever
- **July recorded the highest single-month churn** at 28 customers, confirming a Q3 churn spike likely tied to mid-year budget reviews
- Churned customers had an average NPS of **3.24** compared to **6.98** for active customers, making NPS a strong early warning indicator
- Churned customers raised an average of **5.62 support tickets** vs **2.12** for active customers, indicating that unresolved product issues are a leading driver of churn
- Small businesses account for **134 churned customers** but only **$40K in MRR lost**, while Enterprise accounts for just **7 churned customers** but **$12.7K in MRR lost per segment**, confirming that enterprise churn is low frequency but high financial impact

---

## Technical Challenges and How They Were Solved

### Challenge 1: DAX Measure Circular Dependencies

When building the Power BI dashboard, measures that referenced other measures returned circular dependency errors and failed to calculate. The measures were created in an order that referenced values not yet defined.

**Solution:** Rebuilt all DAX measures in strict dependency order, creating foundational measures like Total Customers and Churned Customers first before creating derived measures like Churn Rate % and Active Customers that depend on them.

### Challenge 2: Waterfall Chart Showing Losses as Gains

Power BI's waterfall chart rendered MRR loss values as positive green bars pointing upward, which contradicted standard financial reporting conventions where losses should appear as red descending bars.

**Solution:** Created a dedicated MRR Loss DAX measure that multiplies churned MRR by -1. Applying this measure to the waterfall chart correctly rendered all monthly loss bars as red and descending, consistent with financial reporting standards.

### Challenge 3: Scatter Plot Data Aggregation

When building the tenure vs MRR scatter plot, Power BI aggregated all 500 customers into just two data points, one for churned and one for active, instead of plotting individual customer dots.

**Solution:** Added customer_id to the Details field well of the scatter plot visual, which forced Power BI to plot one dot per customer rather than aggregating all values into summary points.

### Challenge 4: Binary Churn Labels Across All Visuals

The churned column stored values of 0 and 1 which rendered as numbers in chart legends and axis labels across every visual on all three dashboard pages, making the charts difficult to read without context.

**Solution:** Created a Churn Status calculated column using a DAX IF statement to replace 0 with Active and 1 with Churned. Applied this column consistently across all three pages, replacing the raw binary field in every relevant visual.

---

## Tools and Techniques

**SQL:** SQLite, DB Browser for SQLite, SELECT, WHERE, GROUP BY, ORDER BY, ROUND, COUNT, SUM, AVG, CASE WHEN, CTE (Common Table Expression), RANK() window function

**Power BI:** Power BI Desktop, Power Query, data modeling and table relationships, DAX measures (CALCULATE, DIVIDE, SUM, AVERAGE, COUNTROWS, IF), KPI cards, line chart, bar chart, column chart, donut chart, stacked column chart, waterfall chart, table visual, data labels, custom theme

**Python:** pandas, numpy, sqlite3, datetime, random, reproducible dataset generation with engineered narrative patterns



---

## Author

**Bate Bita Tambe**

Data Analyst

[LinkedIn](https://www.linkedin.com/in/bate-bita-tambe) 
