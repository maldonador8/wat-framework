# WAT Framework

**Workflows · Agents · Tools**: a small automation stack that keeps AI reasoning and code execution in separate layers.

I built and run this at Laiyer8 LLC to operate a production SaaS product (subscription billing, content, social distribution, outreach) with minimal manual work.

## Why this design

An AI agent that does every step itself compounds its error rate: five steps at 90% accuracy each succeed only 59% of the time. WAT splits the work:

| Layer | Lives in | Responsibility |
|---|---|---|
| **Workflows** | `workflows/*.md` | Plain-language SOPs: objective, inputs, which tools to run in what order, expected outputs, edge cases |
| **Agent** | Claude Code | Reads the workflow, decides what to run, handles failures, asks a human when a step is external or irreversible |
| **Tools** | `tools/*.py` | Deterministic Python scripts that do the actual work: API calls, data transforms, file output |

The agent doesn't improvise API calls. It runs a tested script. When a tool fails, the fix goes into the script and the lesson goes into the workflow, so the same failure doesn't happen twice.

### Guardrails

- **Secrets stay in `.env`.** No credentials in code or in git (`.env` is gitignored; see `.env.example`).
- **Human approval for outward actions.** Anything that sends email, posts publicly, or touches production is drafted or previewed first and needs explicit approval.
- **Test one, then batch.** Video renders and email campaigns run on a single item before the full batch.

## Tools

| Script | What it does | Integrations |
|---|---|---|
| `stripe_mrr.py` | MRR / ARR / churn report from live subscription data | Stripe API |
| `content_pipeline.py` | Topic → full content package (posts, email, landing copy) | Anthropic API |
| `ad_copy_generator.py` | Platform-specific ad copy variants | Anthropic API |
| `cold_outreach.py` | Personalized outreach email drafts (generates drafts only; nothing is sent) | Anthropic API |
| `buffer_post.py` | Schedules posts across social platforms | Buffer API |
| `twitter_auth.py` | One-time OAuth 2.0 PKCE setup | X (Twitter) API |
| `twitter_post.py` | Direct posting via OAuth 1.0a | X (Twitter) API |
| `bible_video_generator.py` | AI-generated answer → rendered short-form video | Anthropic API, ffmpeg |
| `bible_video_batch.py` | Batch wrapper around the video generator | |
| `resume_to_docx.py` | Markdown → ATS-friendly Word document | python-docx |

## Workflows

| SOP | Drives |
|---|---|
| `stripe_mrr_dashboard.md` | Revenue reporting |
| `content_to_cash.md` | Content generation → distribution |
| `buffer_social_posting.md` | Scheduled social posting |
| `cold_outreach.md` | Outreach drafting and review |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install anthropic stripe tweepy requests python-docx
cp .env.example .env   # then fill in the keys you need
```

Each tool only needs the keys for the services it calls. See `.env.example` for the full list.

## Tech

Python 3 · Anthropic Claude API · Stripe API · Buffer API · X API (OAuth 1.0a / 2.0 PKCE) · ffmpeg · Claude Code as the orchestrating agent

## About

Built by **Rafael Maldonado**, Cloud Infrastructure Engineer (AWS · Azure · Terraform) and founder of Laiyer8 LLC.
