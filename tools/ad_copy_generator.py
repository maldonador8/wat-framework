#!/usr/bin/env python3
"""
Ad Copy Generator — Bible with AI
===================================
Generates platform-specific ad copy for:
  - Facebook / Instagram (feed, story, reel)
  - Google (search ads — headlines + descriptions)
  - YouTube (15s, 30s, 60s scripts)
  - TikTok (hook + script)
  - Pinterest (pin title + description)

Each ad includes:
  - Primary copy
  - Headline
  - CTA
  - Image prompt (for Midjourney / DALL-E / Canva AI)
  - 3 A/B variants

Usage:
    python tools/ad_copy_generator.py --audience "pastors"
    python tools/ad_copy_generator.py --audience "college students" --platform facebook
    python tools/ad_copy_generator.py --audience "church groups" --platform all --goal subscribers
"""

import os
import sys
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
    print("ERROR: ANTHROPIC_API_KEY not found in .env")
    sys.exit(1)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
MODEL = 'claude-haiku-4-5-20251001'

BRAND = {
    'name': 'Bible with AI',
    'url': 'biblewithai.com',
    'tagline': 'Read, ask, and understand the Bible like never before',
    'price': '$4.99/month or $39.99/year',
    'free_offer': 'Free to read — AI features unlock with subscription',
    'key_features': [
        'Ask any Bible question and get instant, scripture-backed answers',
        'Read in 13 languages including Spanish, Portuguese, French, Hindi',
        'Highlight verses and save personal notes',
        'AI-powered sermon prep for pastors',
        'Daily verses and prayers',
        'Works on any device, no app download needed',
    ]
}

AUDIENCE_ANGLES = {
    'pastors': {
        'pain': 'Sermon prep takes 10+ hours a week',
        'desire': 'More time for your congregation, less time at the desk',
        'hook': 'What if your sermon prep took 2 hours instead of 12?',
        'emotion': 'relief, calling, purpose',
    },
    'college students': {
        'pain': 'Bible feels hard to understand, no one to ask questions',
        'desire': 'Actually understand what you\'re reading',
        'hook': 'Finally understand every verse — ask anything, get answers instantly',
        'emotion': 'curiosity, discovery, belonging',
    },
    'church groups': {
        'pain': 'Hard to prep group study materials, members have different knowledge levels',
        'desire': 'Deeper discussions, everyone engaged',
        'hook': 'Bible study that meets everyone where they are',
        'emotion': 'community, growth, connection',
    },
    'new believers': {
        'pain': 'The Bible feels overwhelming, don\'t know where to start',
        'desire': 'A patient guide that answers every question without judgment',
        'hook': 'New to the Bible? Every question deserves an answer.',
        'emotion': 'welcome, curiosity, faith-building',
    },
    'daily readers': {
        'pain': 'Want to go deeper but don\'t have a study Bible or commentary',
        'desire': 'Richer daily devotions without buying more books',
        'hook': 'Turn your daily reading into daily revelation',
        'emotion': 'depth, consistency, spiritual growth',
    },
    'spanish speakers': {
        'pain': 'Most Bible apps are English-only',
        'desire': 'Study the Bible in their heart language',
        'hook': 'La Biblia con IA — estudia en español, profundiza tu fe',
        'emotion': 'belonging, language pride, accessibility',
    },
}

def call_ai(prompt, max_tokens=1500):
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()

def gen_facebook_instagram(audience, goal, angle):
    prompt = f"""You are a world-class Facebook/Instagram ad copywriter for a Christian tech product.

PRODUCT: {BRAND['name']} — {BRAND['url']}
TAGLINE: {BRAND['tagline']}
PRICE: {BRAND['price']}
FREE OFFER: {BRAND['free_offer']}

AUDIENCE: {audience}
PAIN POINT: {angle['pain']}
DESIRE: {angle['desire']}
HOOK: {angle['hook']}
EMOTIONAL TRIGGERS: {angle['emotion']}
GOAL: {goal}

KEY FEATURES:
{chr(10).join('- ' + f for f in BRAND['key_features'])}

Generate 3 Facebook/Instagram ad variants. For each:

AD VARIANT [1/2/3]:
PRIMARY TEXT (125 chars max, first line is the scroll-stopper):
[copy]

HEADLINE (40 chars max):
[headline]

DESCRIPTION (30 chars max):
[description]

CTA BUTTON: [Subscribe Now / Try Free / Learn More / Get Started]

IMAGE PROMPT (detailed prompt for AI image generation — describe a warm, faith-based scene):
[prompt]

---

Rules:
- No religious clichés ("God is good", "Bless your heart")
- Speak to the PAIN first, then the solution
- Mobile-first: hook in first 3 words
- Variant 1: Emotional (pain/desire)
- Variant 2: Social proof / curiosity angle
- Variant 3: Offer/value angle (price or free tier)"""
    return call_ai(prompt, max_tokens=1800)

def gen_google_ads(audience, goal, angle):
    prompt = f"""Write Google Search Ads for {BRAND['name']} ({BRAND['url']}).

AUDIENCE: {audience}
GOAL: {goal}
PAIN: {angle['pain']}
HOOK: {angle['hook']}

Generate 3 complete Google Search Ad sets:

AD SET [1/2/3]:
HEADLINES (15 options, max 30 chars each — Google picks the best combos):
1. [headline]
2. [headline]
... (15 total)

DESCRIPTIONS (4 options, max 90 chars each):
1. [description]
2. [description]
3. [description]
4. [description]

KEYWORDS (10 high-intent keywords for this audience):
[keyword list]

---
Rules:
- Include {BRAND['url']} naturally in at least 2 headlines
- Mix branded + pain-point + feature headlines
- Descriptions must include a CTA
- Keywords: mix exact match intent (bible study app, ask bible questions, etc.)"""
    return call_ai(prompt, max_tokens=1500)

def gen_youtube_script(audience, goal, angle):
    prompt = f"""Write YouTube ad scripts for {BRAND['name']} ({BRAND['url']}).

AUDIENCE: {audience}
PAIN: {angle['pain']}
DESIRE: {angle['desire']}
HOOK: {angle['hook']}

Write 3 script lengths:

--- 15-SECOND SCRIPT (skip-proof — must hook in first 5 seconds) ---
[HOOK - 5 seconds]: [spoken text]
[MIDDLE - 7 seconds]: [spoken text]
[CTA - 3 seconds]: [spoken text]
VISUAL DIRECTION: [what appears on screen]

--- 30-SECOND SCRIPT ---
[HOOK - 5s]: [text]
[PROBLEM - 8s]: [text]
[SOLUTION - 10s]: [text]
[CTA - 7s]: [text]
VISUAL DIRECTION: [screen description]

--- 60-SECOND SCRIPT ---
[HOOK - 5s]: [text]
[STORY/PROBLEM - 20s]: [text]
[SOLUTION DEMO - 20s]: [text]
[SOCIAL PROOF - 8s]: [text]
[CTA - 7s]: [text]
VISUAL DIRECTION: [screen description]

Rules:
- Hook must make someone stop scrolling
- Speak directly to {audience}
- Mention biblewithai.com in every script
- Tone: warm, genuine, not preachy"""
    return call_ai(prompt, max_tokens=1500)

def gen_tiktok(audience, goal, angle):
    prompt = f"""Write TikTok ad scripts for {BRAND['name']} ({BRAND['url']}).

AUDIENCE: {audience}
HOOK: {angle['hook']}
PAIN: {angle['pain']}

Generate 3 TikTok ad concepts (15-30 seconds each):

CONCEPT [1/2/3]:
HOOK (first 2 seconds — text overlay + spoken): [text]
FORMAT: [talking head / screen recording / text-on-screen / voiceover]
SCRIPT: [full spoken script, 50-80 words]
ON-SCREEN TEXT OVERLAYS: [list the text that appears]
TRENDING SOUND DIRECTION: [describe audio vibe — uplifting, peaceful, curious, etc.]
HASHTAGS (5-8): [hashtags]
CTA AT END: [spoken + on-screen]

Rules:
- First 2 seconds MUST be a pattern interrupt
- TikTok audience is younger — keep it real, not churchy
- Screen recording of the app works great for this product
- End with biblewithai.com on screen"""
    return call_ai(prompt, max_tokens=1500)

def gen_pinterest(audience, goal, angle):
    prompt = f"""Write Pinterest ad copy for {BRAND['name']} ({BRAND['url']}).

AUDIENCE: {audience}
EMOTION: {angle['emotion']}

Generate 5 Pinterest Pin concepts:

PIN [1-5]:
TITLE (100 chars max, keyword-rich): [title]
DESCRIPTION (500 chars max, naturally keyword-rich, soft CTA): [description]
IMAGE CONCEPT (describe a vertical 2:3 image — warm, beautiful, faith-inspired): [concept]
SAVE TRIGGER (why would someone save this?): [reason]

KEYWORD BOARD SUGGESTIONS (5 Pinterest board names to target):
[list]

Rules:
- Pinterest is aspirational — sell the lifestyle, not the product
- Vertical format (1000×1500px ideal)
- Keywords matter more than on other platforms
- Tone: peaceful, hopeful, devotional"""
    return call_ai(prompt, max_tokens=1200)

PLATFORM_GENERATORS = {
    'facebook': ('Facebook / Instagram Ads', gen_facebook_instagram),
    'google': ('Google Search Ads', gen_google_ads),
    'youtube': ('YouTube Ad Scripts', gen_youtube_script),
    'tiktok': ('TikTok Ad Scripts', gen_tiktok),
    'pinterest': ('Pinterest Pin Copy', gen_pinterest),
}

def run():
    parser = argparse.ArgumentParser(description='Ad Copy Generator — Bible with AI')
    parser.add_argument('--audience', default='pastors',
                        choices=list(AUDIENCE_ANGLES.keys()),
                        help='Target audience segment')
    parser.add_argument('--platform', default='facebook',
                        choices=list(PLATFORM_GENERATORS.keys()) + ['all'],
                        help='Ad platform')
    parser.add_argument('--goal', default='subscribers',
                        choices=['subscribers', 'free_trial', 'church_partnership', 'awareness'],
                        help='Campaign goal')
    parser.add_argument('--list-audiences', action='store_true', help='List available audiences')
    args = parser.parse_args()

    if args.list_audiences:
        print("\nAvailable audience segments:")
        for k, v in AUDIENCE_ANGLES.items():
            print(f"  {k:<20} — {v['pain']}")
        return

    audience = args.audience
    angle = AUDIENCE_ANGLES[audience]
    goal = args.goal

    platforms = list(PLATFORM_GENERATORS.keys()) if args.platform == 'all' else [args.platform]

    print(f"\n{'='*60}")
    print(f"  AD COPY GENERATOR — {BRAND['name']}")
    print(f"  Audience:  {audience}")
    print(f"  Platform:  {', '.join(platforms)}")
    print(f"  Goal:      {goal}")
    print(f"{'='*60}\n")

    out_dir = Path(os.path.dirname(__file__)).parent / '.tmp'
    out_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
    out_file = out_dir / f'ads_{timestamp}_{audience}_{args.platform}.md'

    all_output = [f"# Ad Copy — {BRAND['name']}\n**Audience:** {audience} | **Goal:** {goal} | **Generated:** {timestamp}\n"]

    for platform in platforms:
        label, generator = PLATFORM_GENERATORS[platform]
        print(f"Generating {label}...", end=' ', flush=True)
        result = generator(audience, goal, angle)
        section = f"## {label}\n\n{result}"
        all_output.append(section)
        print("done")
        print(f"\n{'-'*60}\n{label.upper()}\n{'-'*60}\n{result}\n")

    with open(out_file, 'w') as f:
        f.write('\n\n---\n\n'.join(all_output))

    print(f"\n{'='*60}")
    print(f"  Saved to: {out_file}")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    run()
