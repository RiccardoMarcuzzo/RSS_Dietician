import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import httpx
import trafilatura
from newspaper import Article as NArticle
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from feed_reader import Article

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (compatible; rss-digest/1.0; '
        '+https://github.com/yourusername/rss-digest)'
    )
}
TIMEOUT = 15 # seconds


def _fetch_html(url: str) -> str:
    try:
        resp = httpx.get(url, headers=HEADERS, timeout=TIMEOUT, 
                         follow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception as exc:
        logger.debug(f'HTTP error {url}: {exc}')
        return ''


def _extract_trafilatura(html: str) -> str:
    try:
        result = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
        )
        return result or ''
    except Exception:
        return ''


def _extract_newspaper(url: str) -> str:
    try:
        art = NArticle(url)
        art.download()
        art.parse()
        return art.text or ''
    except Exception:
        return ''


def _extract_content(article: Article) -> Article:
    html = _fetch_html(article.link)
    if html:
        text = _extract_trafilatura(html)
        if not text or len(text) < 100:
            text = _extract_newspaper(article.link)
    else:
        text = _extract_newspaper(article.link)

    article.content = text.strip() if text else article.summary_rss
    return article


def extract_contents(articles: List[Article], max_workers: int = 8) -> List[Article]:
    with Progress(
        SpinnerColumn(),
        TextColumn('[bold cyan]{task.description}'),
        BarColumn(),
        TaskProgressColumn(),
        transient=True,
    ) as progress:
        task = progress.add_task('Extracting contents...', total=len(articles))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_extract_content, a): a for a in articles}
            results = []
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as exc:
                    art = futures[future]
                    logger.warning(f'Content not extracted {art.link}: {exc}')
                    art.content = art.summary_rss
                    results.append(art)
                finally:
                    progress.advance(task)

    extracted = sum(1 for a in results if len(a.content) > 100)
    logger.info(f'Content extraced: {extracted}/{len(results)}')
    return results, extracted
