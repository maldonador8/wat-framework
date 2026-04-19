#!/usr/bin/env python3
"""
Bible Video Batch Generator
============================
Records 50 videos of biblewithai.com answering 100 Bible questions.
2 questions per video, 1:30-2:00 minutes each.
Full 1280x720 screen recording + worship piano music.

Usage:
    # Generate all 50 videos
    python tools/bible_video_batch.py

    # Generate specific videos (e.g. 1-5 first as test)
    python tools/bible_video_batch.py --videos 1 2 3

    # Regenerate music only
    python tools/bible_video_batch.py --music-only

    # Skip music (no audio)
    python tools/bible_video_batch.py --no-music
"""

import asyncio
import argparse
import math
import os
import shutil
import struct
import subprocess
import sys
import wave
from pathlib import Path
from datetime import datetime

OUT_DIR = Path('/Users/rafaelmaldonado/Library/CloudStorage/OneDrive-Personal/Projects/claude-agents/bible/.tmp')
MUSIC_FILE = OUT_DIR / 'worship_instrumental.wav'
VIDEOS_DIR = OUT_DIR

QUESTION_PAIRS = [
    # Video 1
    ("I am having problems in my marriage. Could you say a prayer for me?",
     "What verses would guide me to have a better relationship with my husband or wife?"),
    # Video 2
    ("I feel lonely even in my marriage. What does God say?",
     "How do I forgive my partner after they hurt me?"),
    # Video 3
    ("I'm thinking about divorce. What should I pray?",
     "How do I love someone who doesn't love me back?"),
    # Video 4
    ("I feel unappreciated by my family. What does the Bible say?",
     "How do I rebuild trust after betrayal?"),
    # Video 5
    ("What does the Bible say about a husband's role?",
     "What does the Bible say about a wife's role?"),
    # Video 6
    ("I'm going through a breakup. What does God say?",
     "I feel like my family is falling apart. What does the Bible say?"),
    # Video 7
    ("I can't stop worrying. What does the Bible say?",
     "I'm scared about my future. Can God calm my fear?"),
    # Video 8
    ("I have panic attacks. Is there a Bible verse for me?",
     "I feel like everything is falling apart. What does God say?"),
    # Video 9
    ("I'm afraid of dying. What does the Bible promise?",
     "I feel overwhelmed and I don't know why. What does God say?"),
    # Video 10
    ("I can't sleep because I'm anxious. What verse helps?",
     "Is it a sin to feel afraid?"),
    # Video 11
    ("I feel like giving up. What does the Bible say?",
     "I've been crying for days. Does God see me?"),
    # Video 12
    ("I feel hopeless. Is there a verse for that?",
     "I'm going through the darkest season of my life. What now?"),
    # Video 13
    ("I feel empty inside. What does God say?",
     "I feel invisible. What does the Bible say about being seen?"),
    # Video 14
    ("I have depression. Am I less faithful because of it?",
     "How did David deal with depression in the Psalms?"),
    # Video 15
    ("I'm starting to doubt God exists. What do I do?",
     "Why do bad things happen to good people?"),
    # Video 16
    ("I prayed and nothing happened. Did God hear me?",
     "I feel far from God. How do I come back?"),
    # Video 17
    ("Can God still use me if I've made terrible mistakes?",
     "I walked away from God for years. Will He take me back?"),
    # Video 18
    ("What does the Bible say when God feels silent?",
     "Is it okay to be angry at God?"),
    # Video 19
    ("I don't know what I'm supposed to do with my life. Help.",
     "I feel worthless. What does God think of me?"),
    # Video 20
    ("I lost my job. What does the Bible say?",
     "I feel like a failure. What does the Bible say?"),
    # Video 21
    ("I'm starting over at 40. Is it too late?",
     "What does the Bible say about following your calling?"),
    # Video 22
    ("I don't feel gifted. Does God still have a plan for me?",
     "I just lost someone I love. What does the Bible say?"),
    # Video 23
    ("I'm angry that God took someone from me. Is that okay?",
     "What happens to our loved ones when they die?"),
    # Video 24
    ("I'm grieving a relationship that ended. What do I pray?",
     "I lost a child. Where is God in this pain?"),
    # Video 25
    ("What did Jesus say about death?",
     "I keep sinning the same sin. Can God forgive me again?"),
    # Video 26
    ("I feel too broken for God to fix. Is that true?",
     "What does the Bible say about shame?"),
    # Video 27
    ("I'm addicted and I can't stop. What does God say?",
     "Does God forgive people who've done terrible things?"),
    # Video 28
    ("How do I forgive someone who isn't sorry?",
     "I feel like I've gone too far from God. Is there a way back?"),
    # Video 29
    ("I hurt someone badly. How do I make it right?",
     "I'm in debt and I'm scared. What does the Bible say?"),
    # Video 30
    ("I can't pay my bills. Does God care?",
     "What does Jesus say about money?"),
    # Video 31
    ("Is it a sin to want financial success?",
     "How do I pray when I don't have words?"),
    # Video 32
    ("What is the most powerful prayer in the Bible?",
     "Does God answer every prayer?"),
    # Video 33
    ("I haven't prayed in years. How do I start again?",
     "What is the book of Psalms really about?"),
    # Video 34
    ("Why did God ask Abraham to sacrifice his son?",
     "What can we learn from the story of Joseph?"),
    # Video 35
    ("What does the book of Job teach us about suffering?",
     "What did Jesus mean by I am the way the truth and the life?"),
    # Video 36
    ("What is the most important verse in the entire Bible?",
     "What does the story of the Prodigal Son teach us?"),
    # Video 37
    ("What was Jesus's final message before He ascended?",
     "How do I build a daily prayer habit?"),
    # Video 38
    ("What does it mean to pray without ceasing?",
     "How do I worship God when I don't feel it?"),
    # Video 39
    ("What does the Bible say about fasting?",
     "What does God say about financial stress?"),
    # Video 40
    ("What does the Bible say about trusting God with money?",
     "What does the Bible say about hard work?"),
    # Video 41
    ("My spouse and I keep arguing. How do I find peace?",
     "What does God say about a broken engagement?"),
    # Video 42
    ("What does the Bible say about loneliness?",
     "How do I find my purpose in God?"),
    # Video 43
    ("What does God say about anxiety and worry?",
     "How do I trust God when things go wrong?"),
    # Video 44
    ("What does the Bible say about healing?",
     "How do I overcome fear with faith?"),
    # Video 45
    ("What does the Bible say about hope?",
     "How do I find joy in difficult times?"),
    # Video 46
    ("What does the Bible say about patience?",
     "How do I deal with jealousy and envy?"),
    # Video 47
    ("What does the Bible say about anger?",
     "How do I deal with a difficult person in my life?"),
    # Video 48
    ("What does the Bible say about pride?",
     "How do I become a more humble person?"),
    # Video 49
    ("What does the Bible say about gratitude?",
     "How do I start reading the Bible for the first time?"),
    # Video 50
    ("What book of the Bible should I read first?",
     "What does it mean to be born again?"),
]

# ─── Worship Music Generator ────────────────────────────────────────────────

SAMPLE_RATE = 44100

def piano_tone(freq, duration, volume=0.3):
    samples = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        envelope = math.exp(-t * 1.8) * volume
        if t < 0.01:
            envelope *= t / 0.01
        val = (math.sin(2 * math.pi * freq * t) +
               math.sin(2 * math.pi * freq * 2 * t) * 0.4 +
               math.sin(2 * math.pi * freq * 3 * t) * 0.15 +
               math.sin(2 * math.pi * freq * (1.002) * t) * 0.3)
        samples.append(val * envelope)
    return samples

def note_freq(name):
    notes = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    n = name[0]
    octave = int(name[-1])
    midi = 12 * (octave + 1) + notes[n]
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))

def add_to_buf(buf, samples, start):
    while len(buf) < start + len(samples):
        buf.append(0.0)
    for i, s in enumerate(samples):
        buf[start + i] += s

def gen_chord(notes, dur, vol=0.22):
    buf = []
    for n in notes:
        t = piano_tone(note_freq(n), dur, vol)
        while len(buf) < len(t):
            buf.append(0.0)
        for i, s in enumerate(t):
            buf[i] += s
    return buf

def generate_worship_music(output_path, duration_sec=135):
    print("Generating worship piano music...", end=' ', flush=True)
    buf = []
    progressions = [
        (['G3','B3','D4','G4'], ['D4','G4','B4']),
        (['D3','F#3','A3','D4'], ['A3','D4','F#4']),
        (['E3','G3','B3','E4'], ['B3','E4','G4']),
        (['C3','E3','G3','C4'], ['G3','C4','E4']),
    ]
    beat = 2.2
    pos = 0
    # Intro
    for note in ['G3','B3','D4','G4','D4','B3']:
        t = piano_tone(note_freq(note), 1.4, 0.18)
        add_to_buf(buf, t, pos)
        pos += int(SAMPLE_RATE * 0.75)

    target = int(SAMPLE_RATE * duration_sec)
    while pos < target:
        for left, right in progressions:
            chord = gen_chord(left, beat * 1.1, 0.2)
            add_to_buf(buf, chord, pos)
            arp_step = beat / (len(right) + 1)
            for j, n in enumerate(right):
                t = piano_tone(note_freq(n), beat * 0.7, 0.26)
                add_to_buf(buf, t, pos + int(SAMPLE_RATE * arp_step * (j + 0.5)))
            pos += int(SAMPLE_RATE * beat)
            if pos >= target:
                break

    # Normalize + simple reverb
    mx = max(abs(s) for s in buf) or 1
    buf = [s / mx * 0.72 for s in buf]
    delay = int(SAMPLE_RATE * 0.08)
    rev = list(buf)
    for i in range(len(rev)):
        if i >= delay:     rev[i] += buf[i - delay] * 0.22
        if i >= delay * 3: rev[i] += buf[i - delay * 3] * 0.10
    mx2 = max(abs(s) for s in rev) or 1
    rev = [s / mx2 * 0.75 for s in rev]

    # Fade out last 5 seconds
    fade_samples = SAMPLE_RATE * 5
    start_fade = len(rev) - fade_samples
    for i in range(fade_samples):
        if start_fade + i < len(rev):
            rev[start_fade + i] *= (1.0 - i / fade_samples)

    with wave.open(str(output_path), 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        for s in rev:
            wf.writeframes(struct.pack('<h', int(max(-1.0, min(1.0, s)) * 32767)))

    print(f"done ({len(rev)/SAMPLE_RATE:.0f}s)")
    return str(output_path)

# ─── Playwright Recording ────────────────────────────────────────────────────

async def wait_for_response(page, prev_count=0):
    prev_len = 0
    stable = 0
    for _ in range(40):
        await page.wait_for_timeout(2000)
        result = await page.evaluate(f"""() => {{
            const msgs = document.querySelectorAll('.message.message-bot');
            const n = msgs.length;
            if (n <= {prev_count}) return {{count: n, len: 0}};
            return {{count: n, len: msgs[n-1].textContent.length}};
        }}""")
        l = result['len']
        if l > 50 and l == prev_len:
            stable += 1
            if stable >= 2:
                return result['count']
        else:
            stable = 0
        prev_len = l
    return await page.evaluate("document.querySelectorAll('.message.message-bot').length")

async def scroll_through_response(page):
    await page.evaluate("""() => {
        const u = document.querySelectorAll('.message.message-user');
        if (u.length) u[u.length-1].scrollIntoView({behavior:'smooth',block:'start'});
    }""")
    await page.wait_for_timeout(2500)
    info = await page.evaluate("""() => {
        const b = document.querySelectorAll('.message.message-bot');
        const last = b[b.length-1];
        if (!last) return {scroll: 0};
        const rect = last.getBoundingClientRect();
        return {scroll: Math.max(0, window.scrollY + rect.bottom + 60 - window.innerHeight)};
    }""")
    total = info.get('scroll', 0)
    if total > 0:
        step = 32
        steps = int(total / step) + 1
        for _ in range(steps):
            await page.evaluate(f"window.scrollBy({{top:{step},behavior:'smooth'}})")
            await page.wait_for_timeout(550)
    await page.wait_for_timeout(4000)

async def record_pair(q1, q2, video_num, tmp_dir):
    """Record one video with two questions on biblewithai.com."""
    from playwright.async_api import async_playwright

    print(f"\n  Video {video_num:02d} — Recording...")
    print(f"    Q1: {q1[:60]}")
    print(f"    Q2: {q2[:60]}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(tmp_dir),
            record_video_size={"width": 1280, "height": 720},
            storage_state={
                "cookies": [],
                "origins": [{
                    "origin": "https://biblewithai.com",
                    "localStorage": [
                        {"name": "bible_tour_seen", "value": "true"},
                        {"name": "bible_tour_completed", "value": "true"},
                        {"name": "bible_free_questions", "value": "0"},
                        {"name": "bible_questions_today", "value": "0"},
                    ]
                }]
            }
        )
        page = await context.new_page()

        # Open chatbot with all limits cleared
        await page.goto("https://biblewithai.com/chatbot.html", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        await page.evaluate("""() => {
            document.querySelectorAll('.tour-overlay,.tour-tooltip,.tour-backdrop,.paywall-modal,.paywall-overlay').forEach(e=>e.remove());
            localStorage.setItem('bible_free_questions','0');
            localStorage.setItem('bible_questions_today','0');
            localStorage.setItem('bible_free_ai_count','0');
            localStorage.setItem('bible_ai_limit_reset','0');
            // Remove any paywall overlays
            document.querySelectorAll('[class*="paywall"],[class*="modal"],[class*="overlay"]').forEach(e=>{
                if(e.style) e.style.display='none';
            });
        }""")
        await page.wait_for_timeout(800)
        # Reload to apply clean state
        await page.reload(wait_until="networkidle")
        await page.wait_for_timeout(2000)
        await page.evaluate("""() => {
            document.querySelectorAll('.tour-overlay,.tour-tooltip,.tour-backdrop,.paywall-modal,.paywall-overlay').forEach(e=>e.remove());
            localStorage.setItem('bible_free_questions','0');
            localStorage.setItem('bible_questions_today','0');
            localStorage.setItem('bible_free_ai_count','0');
            localStorage.setItem('bible_ai_limit_reset','0');
        }""")
        await page.wait_for_timeout(800)

        # Question 1
        print("    Typing Q1...", end=' ', flush=True)
        await page.click('#chatInput', force=True)
        await page.wait_for_timeout(600)
        await page.type('#chatInput', q1, delay=55)
        await page.wait_for_timeout(1800)
        await page.click('#chatSend', force=True)
        await page.wait_for_timeout(2500)
        print("waiting for answer...", end=' ', flush=True)
        bot_count = await wait_for_response(page, 0)
        await page.wait_for_timeout(1500)
        print("scrolling...")
        await scroll_through_response(page)

        # Scroll back to input
        await page.evaluate("""() => {
            const inp = document.querySelector('#chatInput');
            if (inp) inp.scrollIntoView({behavior:'smooth',block:'center'});
        }""")
        await page.wait_for_timeout(1800)

        # Question 2
        print("    Typing Q2...", end=' ', flush=True)
        await page.click('#chatInput', force=True)
        await page.wait_for_timeout(600)
        await page.type('#chatInput', q2, delay=55)
        await page.wait_for_timeout(1800)
        await page.click('#chatSend', force=True)
        await page.wait_for_timeout(2500)
        print("waiting for answer...", end=' ', flush=True)
        await wait_for_response(page, bot_count)
        await page.wait_for_timeout(1500)
        print("scrolling...")
        await scroll_through_response(page)

        # Show footer
        await page.evaluate("window.scrollTo({top:document.body.scrollHeight,behavior:'smooth'})")
        await page.wait_for_timeout(4000)

        video_path = await page.video.path()
        await context.close()
        await browser.close()

    return video_path

def mix_music(video_path, music_path, output_path):
    """Combine video + music with ffmpeg. Loop/trim music to match video length."""
    cmd = [
        'ffmpeg', '-y',
        '-i', str(video_path),
        '-stream_loop', '-1',  # loop music if shorter than video
        '-i', str(music_path),
        '-map', '0:v',
        '-map', '1:a',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '20',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-af', 'volume=0.35',   # music at 35% volume
        '-shortest',
        '-movflags', '+faststart',
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"\n  FFmpeg error: {result.stderr[-300:]}")
        return False
    return True

async def run_async(video_nums, use_music):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate music once
    if use_music:
        if not MUSIC_FILE.exists():
            generate_worship_music(MUSIC_FILE, duration_sec=135)
        else:
            print(f"Music already exists: {MUSIC_FILE}")

    total = len(video_nums)
    done = []

    for i, vid_num in enumerate(video_nums, 1):
        idx = vid_num - 1
        if idx >= len(QUESTION_PAIRS):
            print(f"  Video {vid_num}: out of range, skipping")
            continue

        q1, q2 = QUESTION_PAIRS[idx]
        output_path = VIDEOS_DIR / f'bible_video_{vid_num:02d}.mp4'

        if output_path.exists():
            print(f"  [{i}/{total}] Video {vid_num:02d} already exists, skipping")
            done.append(str(output_path))
            continue

        # Temp dir for playwright raw recording
        import tempfile
        tmp_dir = Path(tempfile.mkdtemp())

        try:
            raw_path = await record_pair(q1, q2, vid_num, tmp_dir)

            # Find the recorded webm
            webm_files = list(tmp_dir.glob('*.webm'))
            if raw_path and os.path.exists(raw_path):
                source = raw_path
            elif webm_files:
                source = webm_files[0]
            else:
                print(f"  Video {vid_num}: no recording found")
                continue

            if use_music:
                print(f"    Mixing music...", end=' ', flush=True)
                ok = mix_music(source, MUSIC_FILE, output_path)
                if ok:
                    size_mb = os.path.getsize(output_path) / 1024 / 1024
                    print(f"done ({size_mb:.1f}MB)")
                    done.append(str(output_path))
                else:
                    # Fall back to converting without music
                    subprocess.run(['ffmpeg', '-y', '-i', str(source),
                                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
                                    '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                                    str(output_path)], capture_output=True)
                    done.append(str(output_path))
            else:
                subprocess.run(['ffmpeg', '-y', '-i', str(source),
                                '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
                                '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                                str(output_path)], capture_output=True)
                size_mb = os.path.getsize(output_path) / 1024 / 1024 if output_path.exists() else 0
                print(f"    Saved ({size_mb:.1f}MB)")
                done.append(str(output_path))

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"\n{'='*55}")
    print(f"  {len(done)}/{total} videos complete")
    print(f"  Saved to: {VIDEOS_DIR}")
    print(f"{'='*55}\n")
    # Open folder
    subprocess.run(['open', str(VIDEOS_DIR)])

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--videos', nargs='*', type=int, help='Specific video numbers 1-50')
    parser.add_argument('--music-only', action='store_true', help='Only generate music file')
    parser.add_argument('--no-music', action='store_true', help='Skip background music')
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    if args.music_only:
        generate_worship_music(MUSIC_FILE)
        subprocess.run(['open', str(MUSIC_FILE)])
        return

    video_nums = args.videos if args.videos else list(range(1, len(QUESTION_PAIRS) + 1))
    use_music = not args.no_music

    print(f"\n{'='*55}")
    print(f"  BIBLE VIDEO BATCH GENERATOR")
    print(f"  Videos to render: {len(video_nums)}")
    print(f"  Music: {'yes' if use_music else 'no'}")
    print(f"  Output: {VIDEOS_DIR}")
    print(f"{'='*55}\n")

    asyncio.run(run_async(video_nums, use_music))

if __name__ == '__main__':
    run()
