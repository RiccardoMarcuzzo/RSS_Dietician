# 📰 RSS Dietician

> Read, group and automatically summarize your RSS feeds with an LLM.
> Output: a navigable HTML digest, divided by news, grouping articles.

---

## How it works

```
config.yml (feeds + configs)
        │
        ▼
[1] Parallel RSS feed reading       ← feedparser
        │
        ▼
[2] Article text extraction         ← trafilatura + newspaper3k (fallback)
        │
        ▼
[3] Topic clustering                ← HDBSCAN on articles' embeddings
        │
        ▼
[4] Relevance scoring              ← recency + coverage + quality
        │
        ▼
[5] LLM summarization per cluster  ← OpenAI / Ollama / Other
        │
        ▼
[6] HTML digest → open in browser
```

---

## Configuration

The only thing you need to write is `config.yml`.

```yaml
# LLM used in summarization
llm:
  model: model-to-use 
  api_key: your-api-key
  base_url: your-model-provider-url

# How many hours going back (0 = all)
hours_lookback: 0

# How many articles per feed (0 = all)
max_articles_per_feed: 0

# Parallelization workers
max_workers: 8

# Output directory
output_dir: ./newspaper

# Telegram (optional: if you want the HTML sent to your Telegram account)
telegram:
  bot_token: your-chatbot-token
  chat_id: your-chatbot-chat-id

feeds:
  - https://feeds.bbci.co.uk/news/world/rss.xml
  - https://rss.nytimes.com/services/xml/rss/nyt/World.xml
```

You can also provide your API key in a .env file:
LLM_MODEL=model-to-use 
LLM_API_KEY=your-api-key
LLM_URL=your-model-provider-url
TELEGRAM_BOT_TOKEN=your-chatbot-token
TELEGRAM_CHAT_ID=your-chatbot-chat-id

---

## Three usage modes

### 1 — How to Install

**Requirements:** Python 3.10+

```bash
git clone https://github.com/RiccardoMarcuzzo/RSS_Dietician.git
cd rss-digest

pip install -r requirements.txt

# Edit config.yml with your feeds
# Then run:
python src/main.py
```

The HTML is saved in `.newspaper/dietician_YYYY.MM.DD_HH.MM.html`.

## Project structure

```
rss-digest/
├── config.yml              ← only file to customize
├── requirements.txt
├── code/
│   ├── main.py              ← entry point
│   ├── config_loader.py     ← reads and validates config.yml
│   ├── feed_reader.py       ← parallel RSS feed reading
│   ├── content_extractor.py ← text extraction from URLs
│   ├── organizer.py         ← clustering
│   ├── llm_summarizer.py    ← multi-provider summaries
│   ├── ranker.py            ← sort news by their relevance score
│   ├── renderer.py          ← HTML template
│   └── telegram_sender.py   ← sents HTML template to telegram chatbot (optional)
└── newspaper/               ← store generated HTML digests (gitignored)
```

---

## Adding custom feeds

This project supports any valid RSS/Atom URL. For personal use you can easily add:

* **YouTube** — each channel has a feed: `https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID`
* **Reddit** — each subreddit: `https://www.reddit.com/r/SUBREDDIT/.rss`
* **Self-published sites** — with tools like [RSSHub](https://rsshub.app/) you can generate feeds from almost any website

---

## Requirements

* Python 3.10+
* API key for the chosen LLM provider (or local Ollama, free)
* Internet connection for feeds and article extraction

---

## License

MIT
