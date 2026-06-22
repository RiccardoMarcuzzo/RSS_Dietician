import hashlib
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from urllib.parse import urlparse

import feedparser
from dateutil import parser as dateparser
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from config_loader import AppConfig, FeedConfig

logger = logging.getLogger(__name__)

@dataclass
class Article:
    id: str
    title: str
    link: str
    source: str
    pub_date: Optional[datetime]
    summary_rss: str = ''
    content: str = ''
    relevance: float = 0.0
    cluster_id: int = -1

def _make_id(link: str) -> str:
    return hashlib.md5(link.encode()).hexdigest()[:12]

def _source_name(url: str) -> str:
    try:
        host = urlparse(url).netloc
        return host.replace('www.', '')
    except Exception:
        return url

def _parse_date(entry) -> Optional[datetime]:
    for attr in ('published', 'updated', 'created'):
        raw = entry.get(attr)
        if raw:
            try:
                dt = dateparser.parse(raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                pass
    return None

def _fetch_feed(
    feed_cfg: FeedConfig, 
    max_articles: int, 
    hours_lookback: int
) -> List[Article]:
    try:
        parsed = feedparser.parse(
            feed_cfg.url, 
            request_headers={'User-Agent': 'rss-dietician/1.0'})
    except Exception as exc:
        logger.warning(f'Errore fetch {feed_cfg.url}: {exc}')
        return []

    source = _source_name(feed_cfg.url)
    cutoff = (datetime.now(timezone.utc) 
              - timedelta(hours=hours_lookback) 
              if hours_lookback > 0 
              else None)
    articles: List[Article] = []

    for entry in parsed.entries:
        if max_articles > 0 and len(articles) >= max_articles:
            break

        link = entry.get('link', '')
        if not link:
            continue

        pub_date = _parse_date(entry)
        if cutoff and pub_date and pub_date < cutoff:
            continue

        summary_rss = (entry.get('summary', '') 
                       or entry.get('description', '') 
                       or '')
        summary_rss = re.sub(r'<[^>]+>', ' ', summary_rss).strip()

        articles.append(Article(
            id=_make_id(link),
            title=entry.get('title', '(no title)').strip(),
            link=link,
            source=source,
            pub_date=pub_date,
            summary_rss=summary_rss[:500],
        ))

    return articles

def fetch_all_feeds(config: AppConfig) -> List[Article]:
    all_articles: List[Article] = []

    with Progress(
        SpinnerColumn(),
        TextColumn('[bold cyan]{task.description}'),
        BarColumn(),
        TaskProgressColumn(),
        transient=True,
    ) as progress:
        task = progress.add_task('Reading feed RSS...', total=len(config.feeds))

        with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
            futures = {
                executor.submit(
                    _fetch_feed, fc, 
                    config.max_articles_per_feed, 
                    config.hours_lookback
                ): fc
                for fc in config.feeds
            }
            for future in as_completed(futures):
                fc = futures[future]
                try:
                    articles = future.result()
                    all_articles.extend(articles)
                    logger.info(f'✓ {fc.url} → {len(articles)} articles')
                except Exception as exc:
                    logger.warning(f'✗ {fc.url}: {exc}')
                finally:
                    progress.advance(task)

    # De-duplication
    seen = set()
    unique = []
    for a in all_articles:
        if a.link not in seen:
            seen.add(a.link)
            unique.append(a)

    logger.info(f'Feed scanned: {len(config.feeds)} | Unique articles: {len(unique)}')
    return unique
