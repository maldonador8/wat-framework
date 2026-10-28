#!/usr/bin/env python3
"""
Cold Outreach Generator
========================
Think and Grow Rich: "Sales is the transfer of enthusiasm." — Napoleon Hill
Rich Dad Poor Dad: "Selling is the #1 skill of an entrepreneur. Most people are poor because
                    they never learned to sell."

Generates hyper-personalized cold outreach emails for:
  - Claude Code consulting (MITech LLC)
  - Bible with AI church/ministry partnerships
  - Any product or service

Uses the AIDA framework: Attention → Interest → Desire → Action
Plus Napoleon Hill's "Burning Desire" close.

Usage:
    python tools/cold_outreach.py \
        --name "John Smith" \
        --company "First Baptist Church" \
        --role "Pastor" \
        --pain "Manual sermon prep taking 10+ hours per week" \
        --product "Bible with AI (biblewithai.com)" \
        --offer "free 30-day church subscription"

    python tools/cold_outreach.py \
        --name "Sarah Chen" \
        --company "TechStart Inc" \
        --role "CTO" \
        --pain "Dev team spending months on features Claude Code could do in hours" \
        --product "Claude Code consulting — MITech LLC" \
        --offer "free 1-hour strategy session"

    # Batch mode: process a CSV file
    python tools/cold_outreach.py --csv prospects.csv --product "Bible with AI"
"""

import os
import sys
import csv
import json
import argparse
from datetime import datetime
from pathlib import Path

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
    import anthropic
except ImportError:
    print("ERROR: anthropic not installed. Run: pip install anthropic")
    sys.exit(1)

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
if not ANTHROPIC_API_KEY:
    print("ERROR: ANTHROPIC_API_KEY not found in environment or .env")
    sys.exit(1)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
MODEL = 'claude-haiku-4-5-20251001'

SENDER_INFO = {
    'name': os.environ.get('INVOICE_NAME', 'Rafael Maldonado'),
    'title': os.environ.get('INVOICE_TITLE', 'Founder'),
    'company': os.environ.get('INVOICE_COMPANY', 'Laiyer8 LLC'),
    'email': os.environ.get('SMTP_EMAIL', ''),
}

def generate_outreach(name, company, role, pain, product, offer, sender=None):
    if sender is None:
        sender = SENDER_INFO

    prompt = f"""You are {sender['name']}, {sender['title']} at {sender['company']}.
Write a cold outreach email to a specific prospect. This must not sound like a template.

PROSPECT:
- Name: {name}
- Company: {company}
- Role: {role}
- Pain point: {pain}

YOUR OFFER:
- Product: {product}
- Specific offer: {offer}

FRAMEWORKS TO USE:
1. AIDA: Attention (1 sentence hook referencing their specific situation) → Interest (how you solve their pain) → Desire (specific outcome they'll get) → Action (one clear ask)
2. Napoleon Hill "Burning Desire": Make them feel the cost of NOT acting
3. Rich Dad: Position this as an asset acquisition, not a purchase

RULES:
- Subject line: under 45 chars, no spam words, highly specific to them
- Email body: 100-150 words MAX. Brevity = respect for their time.
- First sentence: reference something specific about {company} or {role}. NOT generic.
- Never say "I hope this email finds you well"
- Never say "I wanted to reach out"
- One CTA only. Make it frictionless (reply to this email / click one link)
- Sign with {sender['name']}, {sender['title']}, {sender['company']}
- P.S. line: one sentence that adds urgency or social proof

FORMAT:
Subject: [subject line]

[Email body]

[Signature]

P.S. [urgency/social proof line]

---
FOLLOW-UP (send 3 days later if no reply, 50 words max):
Subject: [follow-up subject]

[Follow-up body]"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=700,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()

def process_single(args):
    print(f"\n{'='*60}")
    print(f"  COLD OUTREACH GENERATOR")
    print(f"  Target: {args.name} @ {args.company}")
    print(f"  Product: {args.product}")
    print(f"{'='*60}\n")

    result = generate_outreach(
        name=args.name,
        company=args.company,
        role=args.role,
        pain=args.pain,
        product=args.product,
        offer=args.offer,
    )

    print(result)

    # Save
    out_dir = Path(os.path.dirname(__file__)).parent / '.tmp'
    out_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
    slug = args.name.lower().replace(' ', '_')
    out_file = out_dir / f'outreach_{timestamp}_{slug}.md'

    with open(out_file, 'w') as f:
        f.write(f"# Outreach: {args.name} @ {args.company}\n")
        f.write(f"Generated: {timestamp}\n\n")
        f.write(result)

    print(f"\n\nSaved to: {out_file}")

def process_csv(csv_path, product, offer):
    """
    CSV columns: name, company, role, pain, offer (optional)
    """
    out_dir = Path(os.path.dirname(__file__)).parent / '.tmp'
    out_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
    out_file = out_dir / f'outreach_batch_{timestamp}.md'

    results = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"\nProcessing {len(rows)} prospects...\n")

    with open(out_file, 'w') as out:
        for i, row in enumerate(rows, 1):
            name = row.get('name', '').strip()
            company = row.get('company', '').strip()
            role = row.get('role', '').strip()
            pain = row.get('pain', '').strip()
            row_offer = row.get('offer', offer).strip() or offer

            if not name or not company:
                print(f"  [{i}/{len(rows)}] Skipping — missing name or company")
                continue

            print(f"  [{i}/{len(rows)}] {name} @ {company}...", end=' ', flush=True)

            try:
                result = generate_outreach(name, company, role, pain, product, row_offer)
                out.write(f"# {name} @ {company}\n\n{result}\n\n{'='*60}\n\n")
                print("done")
            except Exception as e:
                print(f"ERROR: {e}")

    print(f"\nBatch saved to: {out_file}")

def run():
    parser = argparse.ArgumentParser(description='Cold Outreach Generator')
    parser.add_argument('--name', help='Prospect first and last name')
    parser.add_argument('--company', help='Prospect company name')
    parser.add_argument('--role', default='Decision Maker', help='Prospect role/title')
    parser.add_argument('--pain', default='inefficiency and wasted time', help='Their core pain point')
    parser.add_argument('--product', required=True, help='Your product/service name')
    parser.add_argument('--offer', default='free consultation', help='Specific offer (free trial, demo, etc)')
    parser.add_argument('--csv', help='Path to CSV file for batch processing')
    args = parser.parse_args()

    if args.csv:
        process_csv(args.csv, args.product, args.offer)
    elif args.name and args.company:
        process_single(args)
    else:
        parser.error("Provide --name and --company for single outreach, or --csv for batch mode")

if __name__ == '__main__':
    run()
