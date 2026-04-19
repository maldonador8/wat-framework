#!/usr/bin/env python3
"""
Stripe MRR Dashboard
====================
Think and Grow Rich principle: "You can't grow what you can't measure."
Rich Dad Poor Dad principle:   "Rich people acquire assets. Know your asset value daily."

Pulls live Stripe data and prints:
  - MRR, ARR, subscriber count by plan
  - Churn rate (last 30 days)
  - Average LTV
  - Top 5 most recent subscribers
  - Revenue trend (last 6 months)

Usage:
    python tools/stripe_mrr.py
    python tools/stripe_mrr.py --json   # machine-readable output
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone
from collections import defaultdict

# Load .env from project root or claude-agents dir
def load_env():
    dirs = [
        os.path.dirname(__file__),
        os.path.join(os.path.dirname(__file__), '..'),
        os.path.join(os.path.dirname(__file__), '..', 'claude-agents'),
    ]
    for d in dirs:
        env_path = os.path.join(d, '.env')
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        os.environ.setdefault(k.strip(), v.strip())

load_env()

try:
    import stripe
except ImportError:
    print("ERROR: stripe not installed. Run: pip install stripe")
    sys.exit(1)

STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
if not STRIPE_SECRET_KEY:
    print("ERROR: STRIPE_SECRET_KEY not found in environment or .env")
    sys.exit(1)

stripe.api_key = STRIPE_SECRET_KEY

def cents_to_dollars(cents):
    return cents / 100.0

def get_all(resource, **kwargs):
    """Auto-paginate through all Stripe results."""
    results = []
    page = resource.list(limit=100, **kwargs)
    while True:
        results.extend(page.data)
        if not page.has_more:
            break
        page = resource.list(limit=100, starting_after=page.data[-1].id, **kwargs)
    return results

def ts_to_dt(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc)

def month_key(ts):
    dt = ts_to_dt(ts)
    return f"{dt.year}-{dt.month:02d}"

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', action='store_true', help='Output JSON instead of table')
    args = parser.parse_args()

    print("Fetching Stripe data...\n")

    # --- Active subscriptions ---
    active_subs = get_all(stripe.Subscription, status='active', expand=['data.items.data.price'])

    # --- Cancelled in last 30 days ---
    import time
    thirty_days_ago = int(time.time()) - (30 * 86400)
    cancelled_subs = get_all(
        stripe.Subscription,
        status='canceled',
        created={'gte': thirty_days_ago}
    )

    # --- MRR calculation ---
    mrr = 0.0
    plan_counts = defaultdict(int)
    plan_mrr = defaultdict(float)

    for sub in active_subs:
        for item in sub['items']['data']:
            price = item.get('price', {})
            unit_amount = price.get('unit_amount', 0) or 0
            interval = price.get('recurring', {}).get('interval', 'month')
            interval_count = price.get('recurring', {}).get('interval_count', 1) or 1
            nickname = price.get('nickname') or price.get('id', 'unknown')
            qty = item.get('quantity', 1) or 1

            # Normalize to monthly
            if interval == 'year':
                monthly = (unit_amount * qty) / (12 * interval_count)
            elif interval == 'week':
                monthly = (unit_amount * qty) * 4.33 / interval_count
            elif interval == 'day':
                monthly = (unit_amount * qty) * 30 / interval_count
            else:
                monthly = (unit_amount * qty) / interval_count

            mrr += monthly
            plan_counts[nickname] += 1
            plan_mrr[nickname] += monthly

    mrr_dollars = cents_to_dollars(mrr)
    arr_dollars = mrr_dollars * 12

    # --- Churn rate ---
    churn_rate = 0.0
    if len(active_subs) > 0:
        churn_rate = len(cancelled_subs) / (len(active_subs) + len(cancelled_subs)) * 100

    # --- LTV estimate (MRR / churn_rate * 100) ---
    ltv = 0.0
    if churn_rate > 0:
        monthly_churn_pct = churn_rate / 100
        # Average revenue per account
        arpa = mrr_dollars / len(active_subs) if active_subs else 0
        ltv = arpa / monthly_churn_pct if monthly_churn_pct > 0 else 0

    # --- Recent subscribers ---
    recent = sorted(active_subs, key=lambda s: s['created'], reverse=True)[:5]

    # --- Monthly revenue trend (invoices last 6 months) ---
    six_months_ago = int(time.time()) - (180 * 86400)
    invoices = get_all(stripe.Invoice, status='paid', created={'gte': six_months_ago})
    monthly_revenue = defaultdict(float)
    for inv in invoices:
        key = month_key(inv['created'])
        monthly_revenue[key] += cents_to_dollars(inv.get('amount_paid', 0))

    sorted_months = sorted(monthly_revenue.items())

    # --- Output ---
    if args.json:
        output = {
            'mrr': round(mrr_dollars, 2),
            'arr': round(arr_dollars, 2),
            'active_subscribers': len(active_subs),
            'cancelled_last_30d': len(cancelled_subs),
            'churn_rate_pct': round(churn_rate, 2),
            'ltv_estimate': round(ltv, 2),
            'plans': {k: {'count': plan_counts[k], 'mrr': round(cents_to_dollars(plan_mrr[k]), 2)} for k in plan_counts},
            'monthly_revenue': dict(sorted_months),
        }
        print(json.dumps(output, indent=2))
        return

    # Pretty print
    divider = "=" * 55
    print(divider)
    print("           STRIPE REVENUE DASHBOARD")
    print(divider)
    print(f"  MRR:                  ${mrr_dollars:>10,.2f}")
    print(f"  ARR:                  ${arr_dollars:>10,.2f}")
    print(f"  Active Subscribers:   {len(active_subs):>10,}")
    print(f"  Cancelled (30d):      {len(cancelled_subs):>10,}")
    print(f"  Churn Rate (30d):     {churn_rate:>9.1f}%")
    if ltv > 0:
        print(f"  Estimated LTV:        ${ltv:>10,.2f}")
    print(divider)

    if plan_counts:
        print("\n  PLANS")
        print(f"  {'Plan':<30} {'Subs':>6}  {'MRR':>10}")
        print("  " + "-" * 50)
        for plan, count in sorted(plan_counts.items(), key=lambda x: -plan_mrr[x[0]]):
            print(f"  {plan:<30} {count:>6}  ${cents_to_dollars(plan_mrr[plan]):>9,.2f}")

    if sorted_months:
        print("\n  MONTHLY REVENUE TREND")
        max_rev = max(v for _, v in sorted_months) or 1
        for month, rev in sorted_months:
            bar_len = int((rev / max_rev) * 30)
            bar = "█" * bar_len
            print(f"  {month}  {bar:<30}  ${rev:,.2f}")

    if recent:
        print("\n  RECENT SUBSCRIBERS")
        for sub in recent:
            email = sub.get('customer_email') or sub.get('customer', '')
            created = ts_to_dt(sub['created']).strftime('%Y-%m-%d')
            print(f"  {created}  {email}")

    print(divider)
    print(f"\n  Run with --json for machine-readable output.")
    print(f"  Key: {'LIVE' if STRIPE_SECRET_KEY.startswith('sk_live') else 'TEST'} mode\n")

if __name__ == '__main__':
    run()
