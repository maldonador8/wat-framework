# Workflow: Content-to-Cash Pipeline

## Objective
Turn any topic or keyword into a full content package — blog post, tweets, LinkedIn, and email — in under 2 minutes. Content is an asset that compounds. One good post can drive subscribers for months.

## Think and Grow Rich Principle Applied
"Specialized knowledge, when organized and intelligently directed through practical plans of action, is worth more than general knowledge." — Napoleon Hill

Your specialized knowledge about AI, the Bible app, Claude Code, entrepreneurship = your content moat. This tool extracts that value and packages it for distribution.

## When to Run
- Weekly content batch: run once, schedule posts across the week
- After a product update or new feature
- When you want to test a new audience angle
- For cold outreach warmup (post first, pitch second)

## Required Inputs
- `ANTHROPIC_API_KEY` in environment
- `anthropic` Python package: `pip install anthropic`

## Tool
```
tools/content_pipeline.py
```

## Usage Examples

### For biblewithai.com
```bash
python tools/content_pipeline.py \
  --topic "How AI is changing Bible study" \
  --product "Bible with AI (biblewithai.com)" \
  --audience "Christians, pastors, and Bible study groups"
```

### For Claude Code consulting (MITech LLC)
```bash
python tools/content_pipeline.py \
  --topic "How I built a SaaS with Claude Code in a weekend" \
  --product "MITech LLC — AI consulting" \
  --audience "startup founders and small business owners"
```

### Skip specific content types
```bash
python tools/content_pipeline.py \
  --topic "Passive income with AI apps" \
  --product "Bible with AI" \
  --skip blog email
```

## Expected Output
- `blog` — 800-word SEO post with H1/H2 structure, PAS intro, meta description
- `tweets` — 3-tweet thread (hook → insight → CTA)
- `linkedin` — 150-250 word founder-voice post with hashtags
- `email` — Subject line + preview + body + CTA, 200-300 words
- All saved to `.tmp/content_YYYY-MM-DD_HHMMSS_topic.md`

## Content Calendar Template (Rich Dad: make your assets work)
| Day | Platform | Topic Angle |
|-----|----------|-------------|
| Mon | LinkedIn | Thought leadership / insight |
| Tue | Twitter  | Engagement / question |
| Wed | Email    | Newsletter value drop |
| Thu | Blog     | SEO long-form |
| Fri | Twitter  | Behind the scenes / win |

## Tips
- Run the same topic with different audiences to get different angles
- Best ROI topics: pain points your product solves, behind-the-scenes builds, data/results
- Repurpose: blog → email → tweets → LinkedIn in one pipeline run
- For biblewithai.com: seasonal topics (Christmas, Easter, Lent) drive huge organic spikes

## Cost
~$0.002 per full pipeline run (Haiku model). Run it 500 times for $1.
