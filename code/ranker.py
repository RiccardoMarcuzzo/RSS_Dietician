from datetime import datetime, timezone
from typing import List, Dict

import numpy as np

from feed_reader import Article

def _relevance_score(articles: List[Article]) -> float:
    now = datetime.now(timezone.utc)
    recency_scores = []
    content_scores = []

    for a in articles:
        if a.pub_date:
            hours_ago = max(0, (now - a.pub_date).total_seconds() / 3600)
            recency_scores.append(np.exp(-hours_ago / 24))
        else:
            recency_scores.append(0.3)
        content_scores.append(min(1.0, len(a.content) / 2000))

    recency    = sum(recency_scores) / len(recency_scores)
    content    = sum(content_scores) / len(content_scores)
    coverage = min(1.0, (len({a.source for a in articles}) - 1) / 4)
    volume     = min(1.0, (len(articles) - 1) / 9)

    score = (
        0.5 * recency
        + 0.3 * coverage
        + 0.1 * volume
        + 0.1 * content
    )
    return round(score, 4)


def rank_news(newspaper: Dict[int, Dict]) -> Dict[int, Dict]:
    scored = [
        {**news, 'relevance': _relevance_score(news['articles'])}
        for news in newspaper.values()
    ]
    scored.sort(key=lambda n: n['relevance'], reverse=True)
    return {i + 1: news for i, news in enumerate(scored)}