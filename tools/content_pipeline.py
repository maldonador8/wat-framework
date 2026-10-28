#!/usr/bin/env python3
"""
Content-to-Cash Pipeline
=========================
Think and Grow Rich: "Specialized Knowledge + organized plans = riches."
Rich Dad Poor Dad: "Content is an asset. It works while you sleep."

Takes a topic/keyword and generates a full content package:
  1. SEO blog post (800-1000 words)
  2. 3 tweets (thread-ready)
  3. LinkedIn post
  4. Email newsletter
  5. Call-to-action for your product

All content is saved to .tmp/ and printed to terminal.

Usage:
    python tools/content_pipeline.py --topic "Bible study app" --product "biblewithai.com"
    python tools/content_pipeline.py --topic "AI for churches" --product "Bible with AI" --audience "pastors"
    python tools/content_pipeline.py --topic "Claude Code consulting" --product "Laiyer8 LLC" --audience "startup founders"
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime
from pathlib import Path

# Load .env
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
MODEL = 'claude-haiku-4-5-20251001'  # Fast + cheap for content

def call_ai(prompt, max_tokens=1200):
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()

def generate_blog_post(topic, product, audience):
    prompt = f"""Write an 800-word SEO blog post about: "{topic}"

Product/brand being promoted: {product}
Target audience: {audience}

Requirements:
- H1 title (compelling, includes the topic keyword)
- 3-4 H2 sections with practical insights
- Use the PAS formula in the intro (Problem, Agitation, Solution)
- 1 mention of {product} naturally woven in as a solution
- End with a clear CTA to try {product}
- Tone: authoritative but conversational
- No fluff, no filler — every sentence earns its place

Output format:
# [Title]

[Full post content with ## subheadings]

---
**SEO Meta Description (155 chars max):** [meta]
**Target keyword:** [keyword]"""
    return call_ai(prompt, max_tokens=1500)

def generate_tweets(topic, product, audience):
    prompt = f"""Write a Twitter/X thread of 3 tweets about: "{topic}"

Product: {product}
Audience: {audience}

Rules:
- Tweet 1: Hook — bold claim or surprising stat. Max 280 chars.
- Tweet 2: The insight — practical value, no fluff. Max 280 chars.
- Tweet 3: CTA — soft sell for {product}. Max 280 chars.
- No hashtag spam (max 1-2 per tweet)
- Write like a founder sharing real insight, not a marketer

Format each tweet as:
Tweet 1: [text]
Tweet 2: [text]
Tweet 3: [text]"""
    return call_ai(prompt, max_tokens=400)

def generate_linkedin(topic, product, audience):
    prompt = f"""Write a LinkedIn post about: "{topic}"

Product: {product}
Audience: {audience}

Requirements:
- First line MUST be a scroll-stopper (no "I'm excited to share...")
- 150-250 words
- Use line breaks generously (LinkedIn formatting)
- Include 1 personal insight or story angle
- Soft CTA for {product} at the end
- 3-5 relevant hashtags at the bottom
- Tone: thought leader, not salesperson

Write the full post ready to copy-paste."""
    return call_ai(prompt, max_tokens=500)

def generate_email(topic, product, audience):
    prompt = f"""Write an email newsletter about: "{topic}"

Product: {product}
Audience: {audience}

Requirements:
- Subject line (under 50 chars, high open rate)
- Preview text (under 90 chars)
- Opening: personal, 1-2 sentences
- Body: 3 short paragraphs of value (no padding)
- 1 clear CTA button text + URL placeholder: [LINK]
- Sign-off: casual founder voice
- Total: 200-300 words

Format:
Subject: [subject]
Preview: [preview]

[Full email body]"""
    return call_ai(prompt, max_tokens=600)

def run():
    parser = argparse.ArgumentParser(description='Content-to-Cash Pipeline')
    parser.add_argument('--topic', required=True, help='Content topic or keyword')
    parser.add_argument('--product', default='my product', help='Your product/brand name')
    parser.add_argument('--audience', default='entrepreneurs and builders', help='Target audience')
    parser.add_argument('--skip', nargs='*', choices=['blog', 'tweets', 'linkedin', 'email'],
                        help='Skip specific content types')
    args = parser.parse_args()

    skip = set(args.skip or [])
    topic = args.topic
    product = args.product
    audience = args.audience

    print(f"\n{'='*55}")
    print(f"  CONTENT-TO-CASH PIPELINE")
    print(f"  Topic:    {topic}")
    print(f"  Product:  {product}")
    print(f"  Audience: {audience}")
    print(f"{'='*55}\n")

    results = {}
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
    slug = topic.lower().replace(' ', '_')[:30]
    out_dir = Path(os.path.dirname(__file__)).parent / '.tmp'
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f'content_{timestamp}_{slug}.md'

    sections = []

    if 'blog' not in skip:
        print("Generating blog post...", end=' ', flush=True)
        blog = generate_blog_post(topic, product, audience)
        results['blog'] = blog
        sections.append(f"# BLOG POST\n\n{blog}")
        print("done")

    if 'tweets' not in skip:
        print("Generating tweets...", end=' ', flush=True)
        tweets = generate_tweets(topic, product, audience)
        results['tweets'] = tweets
        sections.append(f"# TWITTER/X THREAD\n\n{tweets}")
        print("done")

    if 'linkedin' not in skip:
        print("Generating LinkedIn post...", end=' ', flush=True)
        linkedin = generate_linkedin(topic, product, audience)
        results['linkedin'] = linkedin
        sections.append(f"# LINKEDIN POST\n\n{linkedin}")
        print("done")

    if 'email' not in skip:
        print("Generating email newsletter...", end=' ', flush=True)
        email = generate_email(topic, product, audience)
        results['email'] = email
        sections.append(f"# EMAIL NEWSLETTER\n\n{email}")
        print("done")

    # Save to file
    full_content = f"""---
Generated: {timestamp}
Topic: {topic}
Product: {product}
Audience: {audience}
---

""" + "\n\n---\n\n".join(sections)

    with open(out_file, 'w') as f:
        f.write(full_content)

    print(f"\n{'='*55}")
    print(f"  Saved to: {out_file}")
    print(f"{'='*55}\n")

    # Print all content
    print(full_content)

if __name__ == '__main__':
    run()
