# Workflow: Stripe MRR Dashboard

## Objective
Pull live Stripe subscription data and display key SaaS revenue metrics in the terminal. Use this daily to track business health — you can't grow what you can't measure.

## When to Run
- Every morning before working (make it a ritual)
- After any pricing change
- After a marketing push to measure conversion impact
- When preparing for investor or partner conversations

## Required Inputs
- `STRIPE_SECRET_KEY` in `.env` (claude-agents/.env or root .env)
- `stripe` Python package: `pip install stripe`

## Tool
```
tools/stripe_mrr.py
```

## Usage
```bash
# Human-readable dashboard
python tools/stripe_mrr.py

# JSON output (for piping into other tools)
python tools/stripe_mrr.py --json
```

## Expected Output
- **MRR** — Monthly Recurring Revenue (normalized from all plan intervals)
- **ARR** — Annual run rate (MRR × 12)
- **Active subscribers** — count of active Stripe subscriptions
- **Cancelled (30d)** — cancellations in the last 30 days
- **Churn rate** — cancelled / (active + cancelled) × 100
- **LTV estimate** — ARPA / monthly churn rate
- **Plans breakdown** — subscriber count + MRR per pricing tier
- **Monthly revenue trend** — bar chart of last 6 months
- **Recent subscribers** — last 5 new subscribers with emails

## Key Metrics to Monitor (Rich Dad framework)
| Metric | Healthy | Warning | Danger |
|--------|---------|---------|--------|
| MRR growth | +10%/mo | flat | declining |
| Churn rate | <2%/mo | 2–5% | >5% |
| LTV | >12× MRR | 6–12× | <6× |

## Edge Cases
- **Test mode**: Key starting with `sk_test_` shows test data only. Switch to `sk_live_` for production numbers.
- **Multiple prices on one sub**: Each line item is normalized to monthly independently.
- **Annual plans**: Divided by 12 for accurate MRR representation.
- **Zero subscribers**: Tool handles gracefully (no division-by-zero).

## Notes
- Stripe API rate limit: 100 req/s. Auto-pagination is safe for up to ~10,000 subscribers.
- For >10,000 subs, switch to Stripe Sigma (SQL) or export reports via dashboard.
