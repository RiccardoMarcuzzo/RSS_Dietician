# RSS Dietician

> Read, group and automatically summarize your RSS feeds with an LLM.
> Output: a navigable HTML digest, divided by news, grouping articles.

---

## How it works

```
config.yml (feeds + configs)
        │
        ▼
[1] Parallel RSS feed reading      ← feedparser
        │
        ▼
[2] Article text extraction        ← trafilatura + newspaper3k (fallback)
        │
        ▼
[3] Topic clustering               ← HDBSCAN on articles' embeddings
        │
        ▼
[4] LLM summarization per cluster  ← OpenAI / Ollama / Other
        │
        ▼
[5] Relevance scoring              ← recency + coverage + quality
        │
        ▼
[6] HTML digest
        │
        ▼
[Optional] Telegram notification   → send RSS feed directly on phone

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
```
LLM_MODEL=model-to-use 
LLM_API_KEY=your-api-key
LLM_URL=your-model-provider-url
TELEGRAM_BOT_TOKEN=your-chatbot-token
TELEGRAM_CHAT_ID=your-chatbot-chat-id
```

---

## How to install
You can either clone the repository or use a docker container.

### Cloning the repository

**Requirements:** Python 3.14+

```bash
git clone https://github.com/RiccardoMarcuzzo/RSS_Dietician.git && git lfs pull
cd rss-digest

pip install -r requirements.txt

# Edit config.yml with your feeds
# Then run:
python code/main.py
```

The HTML will be saved in `.newspaper/dietician_YYYY.MM.DD_HH.MM.html`.

### Docker

**Requirements:** Docker + Docker compose

First, create a folder "RSS_Dietician". Then, move inside the folder and copy
this docker-compose.yml file:

```yaml
---
services:
  rss-dietician:
    image: snoopywritesstories/rss-dietician:latest
    container_name: rss-dietician
    env_file: .env
    volumes:
      - ./newspaper:/app/newspaper
      - ./config.yml:/app/config.yml
    restart: unless-stopped

  scheduler:
    image: mcuadros/ofelia:latest
    container_name: rss-scheduler
    depends_on:
      - rss-dietician
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: daemon --docker
    restart: unless-stopped
    labels:
      ofelia.job-exec.morning.schedule: "0 8 * * *"
      ofelia.job-exec.morning.container: "rss-dietician"
      ofelia.job-exec.morning.command: "python code/main.py"
      ofelia.job-exec.evening.schedule: "0 18 * * *"
      ofelia.job-exec.evening.container: "rss-dietician"
      ofelia.job-exec.evening.command: "python code/main.py"
```
You can configure the scheduler at your needs. Then, create a .env file with
the following variables:
```
LLM_MODEL=model-to-use 
LLM_API_KEY=your-api-key
LLM_URL=your-model-provider-url
TELEGRAM_BOT_TOKEN=your-chatbot-token
TELEGRAM_CHAT_ID=your-chatbot-chat-id
```
You must also create a .config file. You can copy the .config file in this repo.
Finally, run these commands:
```bash
cd RSS_Dietician
docker compose up -d
```
The HTML will be saved in the volume provided. 

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
