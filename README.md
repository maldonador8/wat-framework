# WAT Framework

**Workflows · Agents · Tools** — separation-of-concerns automation stack.

Probabilistic AI handles reasoning. Deterministic code handles execution. That split is what makes the system reliable.

## Layers

- **Workflows** (`workflows/`) — Markdown SOPs. Objective, inputs, tool sequence, expected outputs, edge cases.
- **Agents** — The decision-maker (you + Claude). Reads the workflow, calls tools in order, recovers from failures.
- **Tools** (`tools/`) — Python scripts that do the actual work. API calls, data transforms, file ops.

Why: chaining 5 steps at 90% accuracy each = 59% success. Offloading execution to deterministic scripts keeps the success rate up.

## Tools

| Script | Purpose |
|---|---|
| `ad_copy_generator.py` | Platform-specific ad copy generator (Bible with AI) |
| `bible_video_batch.py` | Batch-records 50 screen-capture videos answering Bible questions |
| `bible_video_generator.py` | Single-video generator: AI answer + screen recording |
| `buffer_post.py` | Auto-post to Buffer → distributes to social platforms |
| `cold_outreach.py` | Hyper-personalized cold email generator (AIDA + Napoleon Hill close) |
| `content_pipeline.py` | Content-to-Cash: topic → full content package |
| `resume_to_docx.py` | Markdown resume → ATS-friendly .docx |
| `stripe_mrr.py` | Live Stripe MRR/ARR/churn dashboard |
| `twitter_auth.py` | Twitter/X OAuth 2.0 PKCE one-time setup |
| `twitter_post.py` | Direct Twitter/X posting via OAuth 1.0a |

## Workflows

- `buffer_social_posting.md`
- `cold_outreach.md`
- `content_to_cash.md`
- `stripe_mrr_dashboard.md`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install anthropic stripe tweepy requests
cp .env.example .env  # add your keys
```

Required env vars (set in `.env`):

```
ANTHROPIC_API_KEY=
STRIPE_SECRET_KEY=
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=
TWITTER_CLIENT_ID=
TWITTER_CLIENT_SECRET=
BUFFER_ACCESS_TOKEN=
```

## Sync from working copy

The live working copy lives at `~/Library/CloudStorage/OneDrive-Personal/Projects/{tools,workflows}/`. To pull latest changes into this git repo:

```bash
cd ~/code/wat-framework
rsync -av --delete "$HOME/Library/CloudStorage/OneDrive-Personal/Projects/tools/" tools/
rsync -av --delete "$HOME/Library/CloudStorage/OneDrive-Personal/Projects/workflows/" workflows/
git add -A && git commit -m "sync: pull latest from working copy" && git push
```
