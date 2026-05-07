"""
PulseHQ Customer Churn Dataset Generator
=========================================
Generates realistic SaaS churn data for the SaaS-Customer-Churn-Analysis project.
Outputs: customers.csv, monthly_mrr.csv, pulsehq_churn.db (SQLite)

Narrative baked into the data:
- Monthly contract customers churn at ~2x the rate of annual customers
- Basic plan has highest churn rate (~35%) but lowest revenue impact
- Enterprise plan has lowest churn rate (~12%) but highest MRR loss per customer
- Q3 (July-September) is the worst quarter - visible churn spike
- Short tenure customers (<3 months) churn disproportionately (onboarding problem)
- High support ticket volume strongly correlates with churn
- Low NPS scores (below 6) are heavily concentrated in churned customers
"""

import pandas as pd
import numpy as np
import random
import sqlite3
from datetime import datetime, timedelta

# ============================================================
# SEED FOR REPRODUCIBILITY
# ============================================================
np.random.seed(42)
random.seed(42)

# ============================================================
# CONFIGURATION
# ============================================================
START_DATE = datetime(2024, 1, 1)
END_DATE   = datetime(2024, 12, 31)
N_CUSTOMERS = 500

PLANS = {
    'Basic':        {'mrr_min': 99,   'mrr_max': 299,  'base_churn': 0.35},
    'Professional': {'mrr_min': 499,  'mrr_max': 999,  'base_churn': 0.20},
    'Enterprise':   {'mrr_min': 1499, 'mrr_max': 3999, 'base_churn': 0.12},
}

COMPANY_SIZES = ['Small', 'Mid-Market', 'Enterprise']
CONTRACT_TYPES = ['Monthly', 'Annual']
INDUSTRIES = [
    'Technology', 'Finance', 'Healthcare',
    'Retail', 'Manufacturing', 'Education', 'Real Estate'
]

# Q3 churn spike: months 7, 8, 9 carry higher churn weight
# Index 0 = January, Index 11 = December
CHURN_MONTH_WEIGHTS = [0.04, 0.04, 0.05, 0.06, 0.07, 0.08,
                       0.16, 0.15, 0.14, 0.08, 0.07, 0.06]

# ============================================================
# HELPER: COMPANY NAME GENERATOR
# ============================================================
PREFIXES  = ['Apex', 'Nova', 'Bright', 'Core', 'Delta', 'Echo', 'Fusion',
             'Global', 'Hyper', 'Innov', 'Kore', 'Lumix', 'Metro', 'Nexus',
             'Orbit', 'Peak', 'Quantum', 'Rapid', 'Swift', 'Titan', 'Ultra',
             'Vertex', 'Wave', 'Xcel', 'Zenith', 'Arc', 'Bold', 'Crest', 'Drift', 'Edge']
SUFFIXES  = ['Solutions', 'Systems', 'Technologies', 'Group', 'Corp',
             'Partners', 'Ventures', 'Labs', 'Digital', 'Analytics',
             'Dynamics', 'Innovations', 'Services', 'Consulting', 'Networks']
used_names = set()

def generate_company_name():
    for _ in range(100):
        name = f"{random.choice(PREFIXES)} {random.choice(SUFFIXES)}"
        if name not in used_names:
            used_names.add(name)
            return name
    return f"Company {len(used_names) + 1}"


# ============================================================
# GENERATE CUSTOMER RECORDS
# ============================================================
records = []

for i in range(1, N_CUSTOMERS + 1):

    # --- Signup date: weighted toward earlier months (growth phase) ---
    signup_month_weights = [0.10, 0.09, 0.09, 0.08, 0.08, 0.08,
                            0.08, 0.08, 0.08, 0.09, 0.08, 0.07]
    signup_month = int(np.random.choice(range(1, 13), p=signup_month_weights))
    signup_day   = random.randint(1, 28)
    signup_date  = datetime(2024, signup_month, signup_day)

    # --- Company size: skewed toward small businesses ---
    company_size = str(np.random.choice(COMPANY_SIZES, p=[0.55, 0.30, 0.15]))

    # --- Plan: correlated with company size ---
    plan_probs = {
        'Small':      [0.70, 0.25, 0.05],
        'Mid-Market': [0.20, 0.60, 0.20],
        'Enterprise': [0.05, 0.25, 0.70],
    }
    subscription_plan = str(np.random.choice(list(PLANS.keys()), p=plan_probs[company_size]))

    # --- Contract type: annual more common at higher tiers ---
    contract_probs = {
        'Basic':        [0.75, 0.25],   # 75% monthly
        'Professional': [0.50, 0.50],
        'Enterprise':   [0.25, 0.75],   # 75% annual
    }
    contract_type = str(np.random.choice(CONTRACT_TYPES, p=contract_probs[subscription_plan]))

    # --- MRR ---
    mrr = round(random.uniform(PLANS[subscription_plan]['mrr_min'],
                               PLANS[subscription_plan]['mrr_max']), 2)

    # --- Churn probability ---
    base_churn = PLANS[subscription_plan]['base_churn']

    contract_mod = 1.8 if contract_type == 'Monthly' else 0.6

    tenure_months = max(1, (END_DATE - signup_date).days // 30)
    if tenure_months <= 3:
        tenure_mod = 1.5      # onboarding problem
    elif tenure_months <= 6:
        tenure_mod = 1.1
    else:
        tenure_mod = 0.9

    churn_prob = min(0.85, base_churn * contract_mod * tenure_mod)
    churned    = 1 if random.random() < churn_prob else 0

    # --- Churn date: must be after signup and concentrated in Q3 ---
    churn_date = None
    if churned:
        valid_months = list(range(signup_month + 1, 13))
        if not valid_months:
            # Customer signed up in December — no room to churn this year
            churned = 0
        else:
            raw_weights = CHURN_MONTH_WEIGHTS[signup_month:]   # months after signup
            total = sum(raw_weights)
            if total == 0:
                churned = 0
            else:
                norm_weights = [w / total for w in raw_weights]
                churn_month  = int(np.random.choice(valid_months, p=norm_weights))
                churn_day    = random.randint(1, 28)
                churn_date   = datetime(2024, churn_month, churn_day)

    # --- Support tickets: churned customers raise significantly more ---
    support_tickets = int(np.random.poisson(6 if churned else 2))

    # --- NPS score: low NPS concentrates in churned customers ---
    if churned:
        nps_score = int(np.clip(np.random.normal(3.5, 1.8), 0, 10))
    else:
        nps_score = int(np.clip(np.random.normal(7.5, 1.5), 0, 10))

    # --- Last login: churned customers went quiet before leaving ---
    if churned and churn_date:
        days_since_churn = (END_DATE - churn_date).days
        last_login_days_ago = days_since_churn + random.randint(10, 45)
    else:
        last_login_days_ago = random.randint(1, 14)

    records.append({
        'customer_id':               f'CUST-{i:04d}',
        'company_name':              generate_company_name(),
        'industry':                  random.choice(INDUSTRIES),
        'company_size':              company_size,
        'subscription_plan':         subscription_plan,
        'contract_type':             contract_type,
        'monthly_recurring_revenue': mrr,
        'signup_date':               signup_date.strftime('%Y-%m-%d'),
        'churn_date':                churn_date.strftime('%Y-%m-%d') if churn_date else None,
        'churned':                   churned,
        'tenure_months':             tenure_months,
        'support_tickets_raised':    support_tickets,
        'last_login_days_ago':       last_login_days_ago,
        'nps_score':                 nps_score,
        'cohort_month':              signup_date.strftime('%Y-%m'),
    })

df_customers = pd.DataFrame(records)


# ============================================================
# GENERATE MONTHLY MRR SUMMARY TABLE
# ============================================================
monthly_rows = []

for month in range(1, 13):
    month_start = datetime(2024, month, 1)
    month_end   = datetime(2024, month + 1, 1) if month < 12 else datetime(2025, 1, 1)

    signup_dates = pd.to_datetime(df_customers['signup_date'])
    churn_dates  = pd.to_datetime(df_customers['churn_date'].fillna('2099-01-01'))

    # Active = signed up before end of month AND (not churned OR churned after month start)
    active_mask = (signup_dates < month_end) & (churn_dates >= month_start)
    active_df   = df_customers[active_mask]

    # New this month
    new_mask = (signup_dates >= month_start) & (signup_dates < month_end)
    new_df   = df_customers[new_mask]

    # Churned this month
    churned_mask = (
        (df_customers['churned'] == 1) &
        (churn_dates >= month_start) &
        (churn_dates < month_end)
    )
    churned_df = df_customers[churned_mask]

    churn_rate = (
        round(len(churned_df) / len(active_df) * 100, 2)
        if len(active_df) > 0 else 0.0
    )

    monthly_rows.append({
        'month':              month_start.strftime('%Y-%m'),
        'month_number':       month,
        'month_label':        month_start.strftime('%b %Y'),
        'active_customers':   len(active_df),
        'new_customers':      len(new_df),
        'churned_customers':  len(churned_df),
        'total_mrr':          round(active_df['monthly_recurring_revenue'].sum(), 2),
        'new_mrr':            round(new_df['monthly_recurring_revenue'].sum(), 2),
        'churned_mrr':        round(churned_df['monthly_recurring_revenue'].sum(), 2),
        'monthly_churn_rate': churn_rate,
    })

df_mrr = pd.DataFrame(monthly_rows)


# ============================================================
# SAVE OUTPUTS
# ============================================================
df_customers.to_csv('customers.csv', index=False)
df_mrr.to_csv('monthly_mrr.csv', index=False)

conn = sqlite3.connect('pulsehq_churn.db')
df_customers.to_sql('customers',   conn, if_exists='replace', index=False)
df_mrr.to_sql('monthly_mrr',       conn, if_exists='replace', index=False)
conn.close()


# ============================================================
# NARRATIVE VALIDATION — check the story is intact
# ============================================================
print("=" * 55)
print("  PulseHQ Dataset Generated Successfully")
print("=" * 55)
print(f"\n  Total customers  : {len(df_customers)}")
print(f"  Churned          : {df_customers['churned'].sum()}")
print(f"  Overall churn    : {df_customers['churned'].mean()*100:.1f}%")

print("\n  Churn rate by plan:")
for plan, grp in df_customers.groupby('subscription_plan'):
    print(f"    {plan:<15} {grp['churned'].mean()*100:.1f}%")

print("\n  Churn rate by contract type:")
for ct, grp in df_customers.groupby('contract_type'):
    print(f"    {ct:<10} {grp['churned'].mean()*100:.1f}%")

print("\n  Monthly churn rate (Q3 spike check):")
for _, row in df_mrr.iterrows():
    bar = "#" * int(row['monthly_churn_rate'])
    print(f"    {row['month_label']:<10} {row['monthly_churn_rate']:5.1f}%  {bar}")

print("\n  Avg NPS — churned vs active:")
print(f"    Churned : {df_customers[df_customers['churned']==1]['nps_score'].mean():.2f}")
print(f"    Active  : {df_customers[df_customers['churned']==0]['nps_score'].mean():.2f}")

print("\n  Avg support tickets — churned vs active:")
print(f"    Churned : {df_customers[df_customers['churned']==1]['support_tickets_raised'].mean():.2f}")
print(f"    Active  : {df_customers[df_customers['churned']==0]['support_tickets_raised'].mean():.2f}")

print("\n  Files saved:")
print("    customers.csv")
print("    monthly_mrr.csv")
print("    pulsehq_churn.db")
print("=" * 55)
