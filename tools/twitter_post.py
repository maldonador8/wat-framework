#!/usr/bin/env python3
"""
Twitter/X Auto-Poster — Bible with AI
=======================================
Posts tweets directly to your Twitter/X account using OAuth 1.0a.

Usage:
    # Post a single tweet now
    python tools/twitter_post.py --text "Your tweet here"

    # Post a thread
    python tools/twitter_post.py --thread "Tweet 1" "Tweet 2" "Tweet 3"

    # Post from content_pipeline.py output (tweets section)
    python tools/twitter_post.py --from-file .tmp/content_2026-04-06_bible.md

    # Generate + post immediately for an audience
    python tools/twitter_post.py --generate --audience pastors

    # Dry run (preview without posting)
    python tools/twitter_post.py --text "Test" --dry-run
"""

import os
import sys
import re
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
    import tweepy
except ImportError:
    print("ERROR: tweepy not installed. Run: pip install tweepy")
    sys.exit(1)

API_KEY = os.environ.get('TWITTER_API_KEY', '')
API_SECRET = os.environ.get('TWITTER_API_SECRET', '')
ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN', '')
ACCESS_SECRET = os.environ.get('TWITTER_ACCESS_SECRET', '')

if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET]):
    print("ERROR: Missing Twitter credentials in .env")
    print("Required: TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET")
    sys.exit(1)

def get_client():
    return tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_SECRET
    )

def post_tweet(text, dry_run=False, reply_to=None):
    if len(text) > 280:
        print(f"WARNING: Tweet is {len(text)} chars, truncating to 280.")
        text = text[:277] + '...'

    if dry_run:
        print(f"\n[DRY RUN] Would post:\n{text}\n")
        return {'id': 'dry_run'}

    client = get_client()
    kwargs = {}
    if reply_to:
        kwargs['in_reply_to_tweet_id'] = reply_to

    response = client.create_tweet(text=text, **kwargs)
    return response.data

def post_thread(tweets, dry_run=False):
    """Post a list of tweets as a thread."""
    results = []
    reply_to = None

    for i, text in enumerate(tweets):
        print(f"  Tweet {i+1}/{len(tweets)}: ", end='', flush=True)
        result = post_tweet(text, dry_run=dry_run, reply_to=reply_to)
        if result:
            reply_to = result.get('id') if isinstance(result, dict) else result['id']
            tweet_id = reply_to
            print(f"posted (id: {tweet_id})")
            results.append(tweet_id)
        else:
            print("FAILED")
            break

    return results

def parse_tweets_from_file(filepath):
    with open(filepath) as f:
        content = f.read()
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

def run():
    parser = argparse.ArgumentParser(description='Twitter/X Auto-Poster — Bible with AI')
    parser.add_argument('--text', help='Single tweet text')
    parser.add_argument('--thread', nargs='+', help='Post as a thread: --thread "t1" "t2" "t3"')
    parser.add_argument('--from-file', help='Post tweets from content_pipeline output file')
    parser.add_argument('--generate', action='store_true', help='Generate content then post')
    parser.add_argument('--audience', default='pastors', help='Audience for --generate mode')
    parser.add_argument('--topic', help='Custom topic for --generate mode')
    parser.add_argument('--dry-run', action='store_true', help='Preview without posting')
    parser.add_argument('--as-thread', action='store_true', help='Post file tweets as a thread')
    args = parser.parse_args()

    print(f"\n{'='*55}")
    print(f"  TWITTER/X POSTER — Bible with AI")
    print(f"  Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"{'='*55}\n")

    # Generate content first
    if args.generate:
        import subprocess
        topic = args.topic or f"Bible study with AI for {args.audience}"
        print(f"Generating content for: {topic}...")
        script = Path(os.path.dirname(__file__)) / 'content_pipeline.py'
        proc = subprocess.run(
            [sys.executable, str(script),
             '--topic', topic,
             '--product', 'Bible with AI (biblewithai.com)',
             '--audience', args.audience,
             '--skip', 'blog', 'linkedin', 'email'],
            capture_output=True, text=True
        )
        match = re.search(r'Saved to: (.+\.md)', proc.stdout)
        if not match:
            print("ERROR: Failed to generate content")
            print(proc.stderr)
            sys.exit(1)
        args.from_file = match.group(1).strip()
        args.as_thread = True
        print(f"Content saved to: {args.from_file}\n")

    if args.from_file:
        tweets = parse_tweets_from_file(args.from_file)
        if not tweets:
            print("No tweets found in file.")
            sys.exit(1)

        print(f"Found {len(tweets)} tweets:\n")
        for i, t in enumerate(tweets, 1):
            print(f"  [{i}] {t[:100]}{'...' if len(t) > 100 else ''}")

        print()
        if not args.dry_run:
            confirm = input("Post these? [y/n]: ").strip().lower()
            if confirm != 'y':
                print("Cancelled.")
                return

        if args.as_thread:
            print("\nPosting as thread...")
            post_thread(tweets, dry_run=args.dry_run)
        else:
            # Post only the first tweet
            print("\nPosting tweet 1...")
            result = post_tweet(tweets[0], dry_run=args.dry_run)
            if result:
                print(f"Posted: {result}")
        return

    if args.thread:
        print(f"Posting thread ({len(args.thread)} tweets)...")
        post_thread(args.thread, dry_run=args.dry_run)
        return

    if args.text:
        print(f"Posting: {args.text[:80]}...")
        result = post_tweet(args.text, dry_run=args.dry_run)
        if result and not args.dry_run:
            tweet_id = result.get('id') if isinstance(result, dict) else result['id']
            print(f"Posted! ID: {tweet_id}")
            print(f"URL: https://x.com/i/web/status/{tweet_id}")
        return

    parser.print_help()

if __name__ == '__main__':
    run()
