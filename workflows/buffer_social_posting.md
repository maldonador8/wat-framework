# Workflow: Buffer Social Media Auto-Poster

## Objective
Auto-schedule and post Bible with AI content across Twitter/X, Facebook, Instagram, LinkedIn, Pinterest, and TikTok using Buffer as the distribution layer.

## One-Time Setup (10 minutes)

### Step 1: Create Buffer Account
1. Go to https://buffer.com → sign up free
2. Connect your social accounts:
   - Twitter/X (biblewithai or your personal)
   - Facebook Page
   - Instagram Business (must be connected to Facebook Page)
   - LinkedIn Page or Profile
3. Free plan: 3 channels, 10 scheduled posts per channel

### Step 2: Get Your Access Token
1. Go to https://buffer.com/developers/apps
2. Click "Create an App"
   - Name: Bible with AI Publisher
   - Description: Internal content scheduling
   - URL: https://biblewithai.com
3. Copy the **Access Token** shown
4. Add to `.env`:
```
BUFFER_ACCESS_TOKEN=your_token_here
```

### Step 3: Get Your Profile IDs
```bash
python tools/buffer_post.py --list-profiles
```
This shows all connected channels with their IDs. Save them — you'll use them in commands.

---

## Tool
```
tools/buffer_post.py
```

## Usage

### Post a single update (adds to queue)
```bash
python tools/buffer_post.py \
  --text "What if sermon prep took 2 hours instead of 12? Try Bible with AI free → biblewithai.com" \
  --profiles all
```

### Post immediately
```bash
python tools/buffer_post.py --text "Your text" --profiles twitter --now
```

### Schedule for specific time (UTC)
```bash
python tools/buffer_post.py \
  --text "Your text" \
  --profiles twitter,linkedin \
  --schedule "2026-04-07 14:00"
```

### Post from content_pipeline.py output
```bash
# Generate content first
python tools/content_pipeline.py \
  --topic "How AI is changing Bible study" \
  --product "Bible with AI" \
  --audience "Christians and pastors"

# Then post the tweets interactively
python tools/buffer_post.py \
  --from-file .tmp/content_2026-04-06_0157_how_ai_is_changing.md \
  --section tweets \
  --profiles twitter
```

### Full 7-day campaign (generate + schedule automatically)
```bash
python tools/buffer_post.py --campaign --audience pastors --days 7
```
This generates 7 topics, creates content for each, and schedules one post per day at 2pm UTC.

---

## Weekly Content Routine (The Rich Dad Asset Compounding System)

Run this every Monday morning — takes 5 minutes:

```bash
# Generate a full week of content for two audiences
python tools/buffer_post.py --campaign --audience pastors --days 7
python tools/buffer_post.py --campaign --audience "church groups" --days 7
```

Your social media runs on autopilot for the week while you focus on sales.

---

## Best Posting Times by Platform (Bible/Faith audience)
| Platform | Best Time (EST) | Best Days |
|----------|----------------|-----------|
| Facebook | 9am, 1pm | Wed, Fri, Sun |
| Instagram | 8am, 12pm | Mon, Wed, Fri |
| Twitter/X | 8am, 12pm, 6pm | Tue–Thu |
| LinkedIn | 8am, 12pm | Tue, Wed, Thu |
| Pinterest | 8pm, 9pm | Sat, Sun |

---

## Content Mix Strategy (80/20 rule)
- 80% value content (Bible insights, tips, scripture focus)
- 20% promotional (subscribe CTA, church partnerships)

Ratio by post type per week:
- 3 educational/devotional posts
- 2 engagement posts (questions, polls)
- 1 testimonial/social proof
- 1 promotional/CTA

---

## Upgrade Path
- **Free Buffer**: 3 channels, 10 posts/channel/month
- **Buffer Essentials ($6/mo)**: 1 channel, unlimited posts + analytics
- **Buffer Team ($12/mo)**: 8 channels — covers all major platforms

## Notes
- Buffer queues posts — it will distribute them at optimal times if you enable "Optimal Timing"
- Instagram posting requires a Business account (not personal)
- TikTok requires Buffer's paid plan
- Always preview posts in Buffer dashboard before they go live
