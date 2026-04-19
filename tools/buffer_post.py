#!/usr/bin/env python3
"""
Buffer Auto-Poster
==================
Posts content to Buffer, which distributes to:
  - Twitter/X
  - Facebook Page
  - Instagram Business
  - LinkedIn Page
  - Pinterest
  - TikTok (Buffer Business)

Can be used standalone or piped from ad_copy_generator.py / content_pipeline.py

Usage:
    # Setup: list your connected channels
    python tools/buffer_post.py --list-profiles

    # Post a single update now
    python tools/buffer_post.py --text "Your post text" --profiles all

    # Schedule a post
    python tools/buffer_post.py --text "Your post" --profiles twitter,linkedin --schedule "2026-04-07 09:00"

    # Post from a content file (output of content_pipeline.py)
    python tools/buffer_post.py --from-file .tmp/content_2026-04-06_0157_bible_study.md --section tweets

    # Full campaign: generate + schedule a week of posts
    python tools/buffer_post.py --campaign --audience pastors --days 7
"""

import os
import sys
import json
import argparse
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
import urllib.request
import urllib.parse
import urllib.error

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

BUFFER_TOKEN = os.environ.get('BUFFER_ACCESS_TOKEN', '')
BUFFER_API = 'https://api.bufferapp.com/1'

def api_get(endpoint):
    url = f"{BUFFER_API}{endpoint}?access_token={BUFFER_TOKEN}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"API Error {e.code}: {body}")
        return None

def api_post(endpoint, data):
    data['access_token'] = BUFFER_TOKEN
    encoded = urllib.parse.urlencode(data).encode()
    url = f"{BUFFER_API}{endpoint}"
    req = urllib.request.Request(url, data=encoded, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"API Error {e.code}: {body}")
        return None

def check_token():
    if not BUFFER_TOKEN:
        print("\nERROR: BUFFER_ACCESS_TOKEN not set.\n")
        print("How to get your Buffer token:")
        print("  1. Go to https://buffer.com/developers/apps")
        print("  2. Create a new app (name: BibleWithAI, URL: https://biblewithai.com)")
        print("  3. Copy the Access Token")
        print("  4. Add to .env:  BUFFER_ACCESS_TOKEN=your_token_here\n")
        sys.exit(1)

def get_profiles():
    """Return all connected Buffer profiles."""
    result = api_get('/profiles.json')
    if not result:
        return []
    return result

def list_profiles():
    profiles = get_profiles()
    if not profiles:
        print("No profiles found or token invalid.")
        return

    print(f"\n{'='*55}")
    print("  CONNECTED BUFFER CHANNELS")
    print(f"{'='*55}")
    for p in profiles:
        service = p.get('service', 'unknown')
        name = p.get('service_username') or p.get('formatted_username', '')
        pid = p.get('id', '')
        print(f"  {service:<15} {name:<30} {pid}")
    print(f"{'='*55}\n")
    print("Use profile IDs or service names with --profiles flag.")
    print("Example: --profiles twitter,linkedin\n")
    return {p['service']: p['id'] for p in profiles}

def resolve_profile_ids(profiles_arg, all_profiles):
    """Convert service names or 'all' to profile ID list."""
    id_map = {p['service']: p['id'] for p in all_profiles}
    id_map.update({p['id']: p['id'] for p in all_profiles})

    if profiles_arg == 'all':
        return [p['id'] for p in all_profiles]

    result = []
    for name in profiles_arg.split(','):
        name = name.strip()
        if name in id_map:
            result.append(id_map[name])
        else:
            print(f"WARNING: Profile '{name}' not found. Run --list-profiles to see available channels.")
    return result

def schedule_post(text, profile_ids, scheduled_at=None, now=False):
    """Create a Buffer post. scheduled_at is a datetime object or None (adds to queue)."""
    if len(text) > 500:
        print(f"WARNING: Text is {len(text)} chars, may be truncated on some platforms.")

    data = {'text': text}

    # Add each profile_id
    for i, pid in enumerate(profile_ids):
        data[f'profile_ids[{i}]'] = pid

    if now:
        data['now'] = 'true'
    elif scheduled_at:
        ts = int(scheduled_at.timestamp())
        data['scheduled_at'] = str(ts)
    # else: adds to queue (Buffer's default)

    result = api_post('/updates/create.json', data)
    return result

def parse_tweets_from_file(filepath):
    """Extract tweets from content_pipeline output."""
    with open(filepath) as f:
        content = f.read()

    # Find the TWITTER/X THREAD section
    match = re.search(r'# TWITTER/X THREAD\s*\n(.*?)(?:\n---|\Z)', content, re.DOTALL)
    if not match:
        return []

    block = match.group(1)
    tweets = []
    for line in block.split('\n'):
        m = re.match(r'Tweet \d+:\s*(.+)', line.strip())
        if m:
            tweets.append(m.group(1).strip())
    return tweets

def parse_linkedin_from_file(filepath):
    with open(filepath) as f:
        content = f.read()
    match = re.search(r'# LINKEDIN POST\s*\n(.*?)(?:\n---|\Z)', content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def run_campaign(audience, days, all_profiles):
    """Generate content for N days and schedule it in Buffer queue."""
    try:
        import subprocess
        import tempfile
    except ImportError:
        pass

    print(f"\nGenerating {days}-day campaign for audience: {audience}...\n")

    # Topics mapped to audience
    topic_map = {
        'pastors': [
            'How AI is transforming sermon preparation',
            'The future of church technology',
            'Deep Bible study in less time',
            'Why modern pastors embrace digital tools',
            'Serving your congregation better with AI',
            'Bible study resources that work for busy pastors',
            'From hours to minutes: AI-powered sermon prep',
        ],
        'college students': [
            'Understanding the Bible for the first time',
            'AI answers to hard Bible questions',
            'Faith and technology — not opposites',
            'Bible study that fits your college schedule',
            'Every question about the Bible answered',
        ],
        'church groups': [
            'Making small group Bible study deeper',
            'Tools for better group devotions',
            'AI-powered Bible discussion questions',
            'Engage every member in Bible study',
        ],
        'new believers': [
            'Where to start reading the Bible',
            'The most asked Bible questions answered',
            'Understanding scripture as a new Christian',
        ],
        'daily readers': [
            'Going deeper in your daily Bible reading',
            'Bible study habits that last',
            'Turn your morning devotion into revelation',
        ],
        'spanish speakers': [
            'Estudia la Biblia en español con IA',
            'La IA y la fe: juntos por primera vez',
            'Profundiza tu lectura bíblica con tecnología',
        ],
    }

    topics = (topic_map.get(audience) or topic_map['pastors'])[:days]
    profile_ids = [p['id'] for p in all_profiles]

    now = datetime.now(tz=timezone.utc)
    # Post at 9am daily
    post_times = []
    for i in range(days):
        dt = (now + timedelta(days=i+1)).replace(hour=14, minute=0, second=0, microsecond=0)
        post_times.append(dt)

    results = []
    for i, topic in enumerate(topics):
        print(f"Day {i+1}: Generating content for '{topic}'...", end=' ', flush=True)

        # Call content pipeline as subprocess
        out_dir = Path(os.path.dirname(__file__)).parent / '.tmp'
        ts = datetime.now().strftime('%Y%m%d%H%M%S%f')
        tmp_file = out_dir / f'campaign_{ts}.md'

        import subprocess
        script = Path(os.path.dirname(__file__)) / 'content_pipeline.py'
        proc = subprocess.run(
            [sys.executable, str(script),
             '--topic', topic,
             '--product', 'Bible with AI (biblewithai.com)',
             '--audience', audience,
             '--skip', 'blog', 'linkedin', 'email'],
            capture_output=True, text=True
        )

        # Find the saved file
        match = re.search(r'Saved to: (.+\.md)', proc.stdout)
        if not match:
            print("ERROR generating content")
            continue

        content_file = match.group(1).strip()
        tweets = parse_tweets_from_file(content_file)

        if not tweets:
            print("no tweets found")
            continue

        # Post the first tweet (best hook)
        tweet = tweets[0]
        scheduled_at = post_times[i]
        result = schedule_post(tweet, profile_ids, scheduled_at=scheduled_at)

        if result and result.get('success'):
            print(f"scheduled for {scheduled_at.strftime('%Y-%m-%d %H:%M UTC')}")
            results.append({'topic': topic, 'text': tweet, 'scheduled': str(scheduled_at)})
        else:
            print(f"failed: {result}")

        time.sleep(1)  # Rate limit courtesy

    # Save campaign log
    out_dir = Path(os.path.dirname(__file__)).parent / '.tmp'
    log_file = out_dir / f'campaign_log_{datetime.now().strftime("%Y-%m-%d_%H%M")}.json'
    with open(log_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nCampaign scheduled: {len(results)}/{days} posts")
    print(f"Log saved to: {log_file}\n")

def run():
    parser = argparse.ArgumentParser(description='Buffer Auto-Poster for Bible with AI')
    parser.add_argument('--list-profiles', action='store_true', help='List connected Buffer channels')
    parser.add_argument('--text', help='Post text to publish')
    parser.add_argument('--profiles', default='all', help='Comma-separated: twitter,linkedin,facebook or "all"')
    parser.add_argument('--schedule', help='Schedule datetime: "2026-04-07 09:00" (UTC)')
    parser.add_argument('--now', action='store_true', help='Post immediately instead of queuing')
    parser.add_argument('--from-file', help='Post content from a content_pipeline.py output file')
    parser.add_argument('--section', default='tweets', choices=['tweets', 'linkedin'],
                        help='Which section to post from --from-file')
    parser.add_argument('--campaign', action='store_true', help='Generate + schedule a multi-day campaign')
    parser.add_argument('--audience', default='pastors', help='Audience for --campaign mode')
    parser.add_argument('--days', type=int, default=7, help='Number of days for --campaign')
    args = parser.parse_args()

    check_token()

    if args.list_profiles:
        list_profiles()
        return

    all_profiles = get_profiles()
    if not all_profiles:
        print("Could not fetch profiles. Check your BUFFER_ACCESS_TOKEN.")
        sys.exit(1)

    if args.campaign:
        run_campaign(args.audience, args.days, all_profiles)
        return

    profile_ids = resolve_profile_ids(args.profiles, all_profiles)
    if not profile_ids:
        print("No valid profiles found.")
        sys.exit(1)

    scheduled_at = None
    if args.schedule:
        scheduled_at = datetime.strptime(args.schedule, '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)

    if args.from_file:
        filepath = args.from_file
        if args.section == 'tweets':
            posts = parse_tweets_from_file(filepath)
            if not posts:
                print("No tweets found in file.")
                sys.exit(1)
            for i, tweet in enumerate(posts):
                print(f"\nTweet {i+1}:\n{tweet}\n")
                confirm = input("Post this? [y/n/q]: ").strip().lower()
                if confirm == 'q':
                    break
                if confirm == 'y':
                    result = schedule_post(tweet, profile_ids, scheduled_at=scheduled_at, now=args.now)
                    if result and result.get('success'):
                        print("Queued in Buffer.")
                    else:
                        print(f"Failed: {result}")
        elif args.section == 'linkedin':
            post = parse_linkedin_from_file(filepath)
            if not post:
                print("No LinkedIn content found.")
                sys.exit(1)
            print(f"\nLinkedIn Post:\n{post}\n")
            confirm = input("Post this? [y/n]: ").strip().lower()
            if confirm == 'y':
                result = schedule_post(post, profile_ids, scheduled_at=scheduled_at, now=args.now)
                if result and result.get('success'):
                    print("Queued in Buffer.")
                else:
                    print(f"Failed: {result}")
        return

    if args.text:
        result = schedule_post(args.text, profile_ids, scheduled_at=scheduled_at, now=args.now)
        if result and result.get('success'):
            action = 'Posted now' if args.now else ('Scheduled' if scheduled_at else 'Added to queue')
            print(f"{action} successfully.")
            if result.get('updates'):
                for update in result['updates']:
                    print(f"  ID: {update.get('id')} | Status: {update.get('status')}")
        else:
            print(f"Failed: {result}")
        return

    parser.print_help()

if __name__ == '__main__':
    run()
