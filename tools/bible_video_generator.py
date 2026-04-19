#!/usr/bin/env python3
"""
Bible Video Generator
======================
Takes 100 Bible questions, generates 2-sentence AI answers,
then creates 50 scrolling MP4 videos (2 questions per video).

Each video:
  - 1:30 - 2:00 minutes long
  - Dark parchment background with gold text
  - Slow upward scroll so viewers can read comfortably
  - biblewithai.com watermark
  - Renders at 1080x1920 (vertical / TikTok / Reels / Shorts)

Usage:
    # Full run: generate answers + render all 50 videos
    python tools/bible_video_generator.py

    # Step 1 only: generate answers and save to JSON (no video yet)
    python tools/bible_video_generator.py --answers-only

    # Step 2 only: render videos from saved answers JSON
    python tools/bible_video_generator.py --render-only

    # Render specific video numbers
    python tools/bible_video_generator.py --render-only --videos 1 2 3
"""

import os
import sys
import json
import argparse
import textwrap
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

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
    print("ERROR: pip install anthropic"); sys.exit(1)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: pip install Pillow"); sys.exit(1)

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
if not ANTHROPIC_API_KEY:
    print("ERROR: ANTHROPIC_API_KEY not found in .env"); sys.exit(1)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

OUT_DIR = Path(os.path.dirname(__file__)).parent / '.tmp' / 'bible_videos'
ANSWERS_FILE = OUT_DIR / 'answers.json'

# Video dimensions (vertical — TikTok / Reels / Shorts)
VID_W = 1080
VID_H = 1920
FPS = 30
VIDEO_DURATION = 105  # seconds (1:45)

# Design
BG_COLOR = (15, 12, 8)           # near black
GOLD_COLOR = (201, 168, 76)       # gold
WHITE_COLOR = (240, 235, 220)     # warm white
MUTED_COLOR = (160, 150, 130)     # muted for labels
ACCENT_COLOR = (120, 80, 40)      # dark gold for dividers

QUESTIONS = [
    # MARRIAGE & RELATIONSHIPS
    ("I'm having problems in my marriage.", "What does the Bible say?"),
    ("My spouse and I keep arguing.", "How do I find peace?"),
    ("I feel lonely even in my marriage.", "What does God say?"),
    ("How do I forgive my partner after they hurt me?", "What does Scripture say?"),
    ("I'm thinking about divorce.", "What should I pray?"),
    ("How do I love someone who doesn't love me back?", "What does the Bible say?"),
    ("I feel unappreciated by my family.", "What does the Bible say?"),
    ("How do I rebuild trust after betrayal?", "What does God's Word say?"),
    ("What does the Bible say about a husband's role?", ""),
    ("What does the Bible say about a wife's role?", ""),
    ("I'm going through a breakup.", "What does God say?"),
    ("I feel like my family is falling apart.", "What does the Bible say?"),
    # ANXIETY & FEAR
    ("I can't stop worrying.", "What does the Bible say?"),
    ("I'm scared about my future.", "Can God calm my fear?"),
    ("I have panic attacks.", "Is there a Bible verse for me?"),
    ("I feel like everything is falling apart.", "What does God say?"),
    ("I'm afraid of dying.", "What does the Bible promise?"),
    ("I feel overwhelmed and I don't know why.", "What does God say?"),
    ("I can't sleep because I'm anxious.", "What verse helps?"),
    ("Is it a sin to feel afraid?", "What does Scripture say?"),
    # DEPRESSION & SADNESS
    ("I feel like giving up.", "What does the Bible say?"),
    ("I've been crying for days.", "Does God see me?"),
    ("I feel hopeless.", "Is there a verse for that?"),
    ("I'm going through the darkest season of my life.", "What now?"),
    ("I feel empty inside.", "What does God say?"),
    ("I feel invisible.", "What does the Bible say about being seen?"),
    ("I have depression.", "Am I less faithful because of it?"),
    ("How did David deal with depression in the Psalms?", ""),
    # FAITH & DOUBT
    ("I'm starting to doubt God exists.", "What do I do?"),
    ("Why do bad things happen to good people?", "What does the Bible say?"),
    ("I prayed and nothing happened.", "Did God hear me?"),
    ("I feel far from God.", "How do I come back?"),
    ("Can God still use me if I've made terrible mistakes?", ""),
    ("I walked away from God for years.", "Will He take me back?"),
    ("What does the Bible say when God feels silent?", ""),
    ("Is it okay to be angry at God?", "What does Scripture say?"),
    # PURPOSE & IDENTITY
    ("I don't know what I'm supposed to do with my life.", "Help."),
    ("I feel worthless.", "What does God think of me?"),
    ("I lost my job.", "What does the Bible say?"),
    ("I feel like a failure.", "What does the Bible say?"),
    ("I'm starting over at 40.", "Is it too late?"),
    ("What does the Bible say about following your calling?", ""),
    ("I don't feel gifted.", "Does God still have a plan for me?"),
    # GRIEF & LOSS
    ("I just lost someone I love.", "What does the Bible say?"),
    ("I'm angry that God took someone from me.", "Is that okay?"),
    ("What happens to our loved ones when they die?", ""),
    ("I'm grieving a relationship that ended.", "What do I pray?"),
    ("I lost a child.", "Where is God in this pain?"),
    ("What did Jesus say about death?", ""),
    # SIN & FORGIVENESS
    ("I keep sinning the same sin.", "Can God forgive me again?"),
    ("I feel too broken for God to fix.", "Is that true?"),
    ("What does the Bible say about shame?", ""),
    ("I'm addicted and I can't stop.", "What does God say?"),
    ("Does God forgive people who've done terrible things?", ""),
    ("How do I forgive someone who isn't sorry?", ""),
    ("I feel like I've gone too far from God.", "Is there a way back?"),
    ("I hurt someone badly.", "How do I make it right?"),
    # MONEY & PROVISION
    ("I'm in debt and I'm scared.", "What does the Bible say?"),
    ("I can't pay my bills.", "Does God care?"),
    ("What does Jesus say about money?", ""),
    ("Is it a sin to want financial success?", "What does Scripture say?"),
    # PRAYER & WORSHIP
    ("How do I pray when I don't have words?", ""),
    ("What is the most powerful prayer in the Bible?", ""),
    ("Does God answer every prayer?", "What does Scripture say?"),
    ("I haven't prayed in years.", "How do I start again?"),
    # BIBLE BOOKS & STORIES
    ("What is the book of Psalms really about?", ""),
    ("Why did God ask Abraham to sacrifice his son?", ""),
    ("What can we learn from the story of Joseph?", ""),
    ("What does the book of Job teach us about suffering?", ""),
    ("What did Jesus mean by 'I am the way, the truth, and the life'?", ""),
    ("What is the most important verse in the entire Bible?", ""),
    ("What does the story of the Prodigal Son teach us?", ""),
    ("What was Jesus's final message before He ascended?", ""),
]

def get_answer(q1, q2):
    question = f"{q1} {q2}".strip()
    prompt = f"""You are a warm, knowledgeable Bible teacher.

Answer this question in exactly 2 sentences. Be specific — include at least one Bible verse reference (book chapter:verse). Be comforting, direct, and spiritually meaningful. No fluff.

Question: {question}

Answer (2 sentences only):"""

    response = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()

def generate_answers():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing if partial run
    if ANSWERS_FILE.exists():
        with open(ANSWERS_FILE) as f:
            data = json.load(f)
    else:
        data = []

    done_indices = {item['index'] for item in data}
    total = len(QUESTIONS)

    print(f"\nGenerating answers for {total} questions...\n")

    for i, (q1, q2) in enumerate(QUESTIONS):
        if i in done_indices:
            print(f"  [{i+1}/{total}] Skipping (already done)")
            continue

        question_display = f"{q1} {q2}".strip()
        print(f"  [{i+1}/{total}] {question_display[:60]}...", end=' ', flush=True)

        try:
            answer = get_answer(q1, q2)
            data.append({
                'index': i,
                'q1': q1,
                'q2': q2,
                'answer': answer
            })
            # Save after each one
            with open(ANSWERS_FILE, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("done")
        except Exception as e:
            print(f"ERROR: {e}")

    # Sort by index
    data.sort(key=lambda x: x['index'])
    with open(ANSWERS_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nAnswers saved to: {ANSWERS_FILE}")
    return data

def get_font(size, bold=False):
    """Try to load a nice font, fall back to default."""
    font_candidates = [
        '/System/Library/Fonts/Supplemental/Georgia.ttf',
        '/System/Library/Fonts/Georgia.ttf',
        '/Library/Fonts/Georgia.ttf',
        '/System/Library/Fonts/Supplemental/Times New Roman.ttf',
        '/System/Library/Fonts/Times New Roman.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
    ]
    bold_candidates = [
        '/System/Library/Fonts/Supplemental/Georgia Bold.ttf',
        '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
        '/Library/Fonts/Arial Bold.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
    ]
    candidates = bold_candidates if bold else font_candidates
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def wrap_text(text, font, max_width, draw):
    """Word-wrap text to fit max_width pixels."""
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = ' '.join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(' '.join(current))
            current = [word]
    if current:
        lines.append(' '.join(current))
    return lines

def render_content_image(pair):
    """Render a tall image with 2 Q&A pairs for scrolling."""
    q1_data = pair[0]
    q2_data = pair[1]

    padding = 80
    content_width = VID_W - (padding * 2)

    # Fonts
    label_font = get_font(32)
    question_font = get_font(52, bold=True)
    answer_font = get_font(44)
    verse_font = get_font(38)
    watermark_font = get_font(34)
    divider_font = get_font(36)

    # --- Pre-render to measure total height ---
    dummy = Image.new('RGB', (VID_W, 100))
    draw = ImageDraw.Draw(dummy)

    def measure_block(qdata):
        q_full = f"{qdata['q1']} {qdata['q2']}".strip()
        a_text = qdata['answer']

        q_lines = wrap_text(q_full, question_font, content_width, draw)
        a_lines = wrap_text(a_text, answer_font, content_width, draw)

        q_h = sum(draw.textbbox((0,0), l, font=question_font)[3] + 10 for l in q_lines)
        a_h = sum(draw.textbbox((0,0), l, font=answer_font)[3] + 10 for l in a_lines)

        return q_lines, a_lines, q_h, a_h

    q1_lines, a1_lines, q1_h, a1_h = measure_block(q1_data)
    q2_lines, a2_lines, q2_h, a2_h = measure_block(q2_data)

    label_h = 50
    divider_h = 80
    block1_h = label_h + 20 + q1_h + 30 + a1_h
    block2_h = label_h + 20 + q2_h + 30 + a2_h
    watermark_h = 80

    total_h = (VID_H // 2) + block1_h + divider_h + block2_h + (VID_H // 2) + watermark_h + 60

    # --- Render ---
    img = Image.new('RGB', (VID_W, total_h), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Subtle texture lines
    for y in range(0, total_h, 4):
        draw.line([(0, y), (VID_W, y)], fill=(20, 17, 12), width=1)

    y = VID_H // 2  # start content halfway down (so first Q starts at center)

    def draw_block(qdata, q_lines, a_lines, label_num):
        nonlocal y

        # Label
        label = f"Question {label_num}"
        bbox = draw.textbbox((0, 0), label, font=label_font)
        lw = bbox[2] - bbox[0]
        draw.text(((VID_W - lw) // 2, y), label, font=label_font, fill=MUTED_COLOR)
        y += label_h + 20

        # Gold top bar
        draw.rectangle([(padding, y), (VID_W - padding, y + 3)], fill=GOLD_COLOR)
        y += 20

        # Question lines
        for line in q_lines:
            bbox = draw.textbbox((0, 0), line, font=question_font)
            lw = bbox[2] - bbox[0]
            lh = bbox[3] - bbox[1]
            draw.text(((VID_W - lw) // 2, y), line, font=question_font, fill=WHITE_COLOR)
            y += lh + 12
        y += 24

        # Answer lines
        for line in a_lines:
            bbox = draw.textbbox((0, 0), line, font=answer_font)
            lw = bbox[2] - bbox[0]
            lh = bbox[3] - bbox[1]
            draw.text(((VID_W - lw) // 2, y), line, font=answer_font, fill=GOLD_COLOR)
            y += lh + 12
        y += 20

    draw_block(q1_data, q1_lines, a1_lines, q1_data['index'] + 1)

    # Divider
    y += 20
    draw.line([(padding + 80, y + divider_h // 2), (VID_W - padding - 80, y + divider_h // 2)],
              fill=ACCENT_COLOR, width=2)
    cross_x = VID_W // 2
    cross_y = y + divider_h // 2
    draw.line([(cross_x, cross_y - 16), (cross_x, cross_y + 16)], fill=GOLD_COLOR, width=3)
    draw.line([(cross_x - 10, cross_y - 4), (cross_x + 10, cross_y - 4)], fill=GOLD_COLOR, width=3)
    y += divider_h + 20

    draw_block(q2_data, q2_lines, a2_lines, q2_data['index'] + 1)

    # Watermark
    y += 40
    wm = "biblewithai.com"
    bbox = draw.textbbox((0, 0), wm, font=watermark_font)
    ww = bbox[2] - bbox[0]
    draw.text(((VID_W - ww) // 2, y), wm, font=watermark_font, fill=MUTED_COLOR)

    return img, total_h

def render_video(pair, video_num, target_dir):
    """Render a scrolling video from an image using ffmpeg."""
    img, total_h = render_content_image(pair)

    # Scroll distance: from top of content to end
    # We want the scroll to cover the full image over VIDEO_DURATION seconds
    scroll_distance = total_h - VID_H
    if scroll_distance < 0:
        scroll_distance = 0

    pixels_per_second = scroll_distance / VIDEO_DURATION

    # Save image to temp file
    tmp_dir = Path(tempfile.mkdtemp())
    img_path = tmp_dir / 'frame.png'
    img.save(str(img_path), 'PNG')

    out_path = target_dir / f'video_{video_num:02d}.mp4'

    # FFmpeg scrolling filter
    # zoompan or scroll filter to animate
    # We'll use the 'scroll' filter with vertical scrolling
    cmd = [
        'ffmpeg', '-y',
        '-loop', '1',
        '-i', str(img_path),
        '-vf', (
            f"scale={VID_W}:-1,"
            f"crop={VID_W}:{VID_H}:0:'min(n*{pixels_per_second:.4f}/{FPS},{total_h}-{VID_H})',"
            f"setpts=PTS-STARTPTS"
        ),
        '-t', str(VIDEO_DURATION),
        '-r', str(FPS),
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        str(out_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    shutil.rmtree(tmp_dir, ignore_errors=True)

    if result.returncode != 0:
        print(f"\nFFmpeg error: {result.stderr[-500:]}")
        return None

    return out_path

def run():
    parser = argparse.ArgumentParser(description='Bible Video Generator')
    parser.add_argument('--answers-only', action='store_true', help='Only generate answers, no video')
    parser.add_argument('--render-only', action='store_true', help='Only render videos from saved answers')
    parser.add_argument('--videos', nargs='*', type=int, help='Specific video numbers to render (1-50)')
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Generate answers
    if not args.render_only:
        data = generate_answers()
    else:
        if not ANSWERS_FILE.exists():
            print(f"ERROR: {ANSWERS_FILE} not found. Run without --render-only first.")
            sys.exit(1)
        with open(ANSWERS_FILE) as f:
            data = json.load(f)
        data.sort(key=lambda x: x['index'])

    if args.answers_only:
        print("\nAnswers generated. Run without --answers-only to render videos.")
        return

    if len(data) < 2:
        print("Not enough answers to make videos.")
        sys.exit(1)

    # Pair up questions: video 1 = Q1+Q2, video 2 = Q3+Q4, etc.
    pairs = []
    for i in range(0, len(data) - 1, 2):
        pairs.append((data[i], data[i+1]))

    video_dir = OUT_DIR / 'videos'
    video_dir.mkdir(exist_ok=True)

    target_videos = args.videos if args.videos else list(range(1, len(pairs) + 1))

    print(f"\n{'='*55}")
    print(f"  RENDERING {len(target_videos)} VIDEOS")
    print(f"  Output: {video_dir}")
    print(f"{'='*55}\n")

    rendered = []
    for vid_num in target_videos:
        idx = vid_num - 1
        if idx >= len(pairs):
            print(f"  Video {vid_num}: out of range, skipping")
            continue

        pair = pairs[idx]
        q1 = f"{pair[0]['q1']} {pair[0]['q2']}".strip()[:50]
        q2 = f"{pair[1]['q1']} {pair[1]['q2']}".strip()[:50]
        print(f"  [{vid_num}/{len(target_videos)}] {q1[:40]}... + {q2[:40]}...", end=' ', flush=True)

        out = render_video(pair, vid_num, video_dir)
        if out:
            size_mb = os.path.getsize(out) / 1024 / 1024
            print(f"done ({size_mb:.1f}MB)")
            rendered.append(str(out))
        else:
            print("FAILED")

    print(f"\n{'='*55}")
    print(f"  {len(rendered)} videos saved to:")
    print(f"  {video_dir}")
    print(f"{'='*55}\n")

    # Save manifest
    manifest = video_dir / 'manifest.json'
    with open(manifest, 'w') as f:
        json.dump({'videos': rendered, 'generated': str(datetime.now())}, f, indent=2)

    print(f"Manifest: {manifest}\n")

if __name__ == '__main__':
    run()
