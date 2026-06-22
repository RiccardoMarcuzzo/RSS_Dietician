from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from jinja2 import Environment, BaseLoader


TEMPLATE = r"""
<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>RSS Dietician – {{ date }}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&family=Source+Serif+4:ital,wght@0,300;0,400;0,600;1,300;1,400;1,600&display=swap');

  :root {
    --ink:      #1a1209;
    --paper:    #f5f0e8;
    --sepia:    #c8a96e;
    --rust:     #8b3a1a;
    --muted:    #6b5d4f;
    --rule:     #d4c4a8;
    --card:     #fdfaf4;
    --shadow:   rgba(60, 40, 10, .10);
    --accent:   #2a4a6b;
  }

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html { font-size: 16px; scroll-behavior: smooth; }

  body {
    background: var(--paper);
    color: var(--ink);
    font-family: 'Source Serif 4', Georgia, serif;
    font-weight: 300;
    line-height: 1.75;
    min-height: 100vh;
  }

  /* ── Masthead ── */
  .masthead {
    background: var(--ink);
    color: var(--paper);
    text-align: center;
    padding: 3.5rem 2rem 3rem;
    border-bottom: 4px solid var(--sepia);
  }
  .masthead .tagline {
    font-family: 'Source Serif 4', serif;
    font-style: italic;
    font-size: .95rem;
    color: var(--sepia);
    letter-spacing: .08em;
    margin-bottom: .9rem;
  }
  .masthead h1 {
    font-family: 'Playfair Display', serif;
    font-weight: 900;
    font-size: clamp(3rem, 8vw, 5.5rem);
    letter-spacing: -.02em;
    line-height: 1;
  }
  .masthead .meta {
    margin-top: 1.1rem;
    font-size: .82rem;
    color: #a89070;
    letter-spacing: .1em;
    text-transform: uppercase;
  }
  .masthead .meta span {
    display: inline-block;
    margin: 0 .6rem;
  }
  .masthead .meta .sep { color: var(--sepia); }

  /* ── Layout ── */
  .container {
    max-width: 860px;
    margin: 0 auto;
    padding: 3rem 1.5rem 5rem;
  }

  /* ── Divisore ornamentale ── */
  .ornament {
    text-align: center;
    color: var(--sepia);
    font-size: 1.1rem;
    letter-spacing: .5em;
    margin: 2.5rem 0;
    user-select: none;
  }

  /* ── Card notizia ── */
  .news-card {
    background: var(--card);
    border: 1px solid var(--rule);
    border-top: 3px solid var(--sepia);
    padding: 2rem 2.2rem 1.6rem;
    margin-bottom: 2.4rem;
    box-shadow: 0 2px 10px var(--shadow);
    transition: box-shadow .2s;
    position: relative;
  }
  .news-card:hover {
    box-shadow: 0 6px 24px var(--shadow);
  }

  /* Numero progressivo */
  .news-number {
    position: absolute;
    top: -1px;
    right: 1.8rem;
    background: var(--sepia);
    color: var(--ink);
    font-family: 'Playfair Display', serif;
    font-weight: 700;
    font-size: .78rem;
    letter-spacing: .1em;
    padding: .2rem .7rem;
    text-transform: uppercase;
  }

  .news-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.45rem;
    font-weight: 700;
    line-height: 1.25;
    color: var(--ink);
    margin-bottom: 1rem;
    padding-right: 3rem;
  }

  .news-summary {
    font-size: 1rem;
    line-height: 1.8;
    color: #3a2e22;
    font-style: italic;
    border-left: 3px solid var(--rule);
    padding-left: 1.1rem;
    margin-bottom: 1.4rem;
  }

  /* ── Lista fonti ── */
  .sources-label {
    font-size: .72rem;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: .5rem;
    font-style: normal;
    font-family: 'Source Serif 4', serif;
    font-weight: 600;
  }

  .articles-list {
    border-top: 1px solid var(--rule);
    padding-top: .75rem;
    display: flex;
    flex-direction: column;
    gap: .35rem;
  }

  .article-link {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: .8rem;
    font-size: .875rem;
    text-decoration: none;
    color: var(--rust);
    padding: .2rem 0;
    border-bottom: 1px dashed transparent;
    transition: border-color .15s, color .15s;
    font-style: normal;
  }
  .article-link:hover {
    color: var(--ink);
    border-bottom-color: var(--rule);
  }
  .article-link .art-title { flex: 1; }
  .article-link .art-meta {
    font-size: .75rem;
    color: var(--muted);
    white-space: nowrap;
    font-style: italic;
    flex-shrink: 0;
  }

  /* ── Footer ── */
  footer {
    text-align: center;
    padding: 2.5rem 1rem 3rem;
    font-size: .8rem;
    color: var(--muted);
    border-top: 2px solid var(--rule);
  }
  footer .footer-rule {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 1rem;
    color: var(--sepia);
    margin-bottom: .6rem;
  }

  /* ── Responsive ── */
  @media (max-width: 600px) {
    .masthead h1 { font-size: 2.6rem; }
    .news-card { padding: 1.3rem 1.2rem 1.1rem; }
    .article-link .art-meta { display: none; }
    .news-title { font-size: 1.2rem; }
  }
</style>
</head>
<body>

<header class="masthead">
  <p class="tagline">Your curated news diet</p>
  <h1>RSS Dietician</h1>
  <p class="meta">
    <span>{{ date }}</span>
    <span class="sep">·</span>
    <span>{{ total_news }} news</span>
    <span class="sep">·</span>
    <span>{{ total_articles }} articles</span>
  </p>
</header>

<main class="container">

  {% for key, news in newspaper.items() %}

  <article class="news-card">
    <span class="news-number">№ {{ key }}</span>

    <h2 class="news-title">{{ news.title }}</h2>

    <p class="news-summary">{{ news.summary }}</p>

    {% if news.articles %}
    <p class="sources-label">Sources</p>
    <div class="articles-list">
      {% for art in news.articles %}
      <a class="article-link"
         href="{{ art.link | default('#') }}"
         target="_blank"
         rel="noopener">
        <span class="art-title">{{ art.title }}</span>
        <span class="art-meta">
          {{ art.source | default('') }}
          {%- if art.pub_date %} · {{ art.pub_date.strftime('%d/%m %H:%M') }}{% endif %}
        </span>
      </a>
      {% endfor %}
    </div>
    {% endif %}
  </article>

  {% if not loop.last %}
  <div class="ornament">✦ &nbsp; ✦ &nbsp; ✦</div>
  {% endif %}

  {% endfor %}

</main>

<footer>
  <p class="footer-rule">Your curated news diet.</p>
  <p>Generated by <strong>RSS Dietician</strong> &nbsp;·&nbsp; {{ date }}</p>
</footer>

</body>
</html>
"""


def _slugify(text: str) -> str:
    import re
    import unicodedata
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text.lower())
    return re.sub(r'[\s_-]+', '-', text).strip('-')


def render_html(
    newspaper: Dict[int, Dict],
    output_dir: str = 'output',
) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    date_str = now.strftime('%d %B %Y, %H:%M UTC')
    filename = f"dietician_{now.strftime('%Y.%m.%d_%H.%M')}.html"
    out_file = output_path / filename

    total_articles = sum(len(n['articles']) for n in newspaper.values())
    total_news = len(newspaper)

    env = Environment(loader=BaseLoader())
    env.filters['slugify'] = _slugify
    tmpl = env.from_string(TEMPLATE)

    html = tmpl.render(
        date=date_str,
        newspaper=newspaper,
        total_news=total_news,
        total_articles=total_articles,
    )

    out_file.write_text(html, encoding='utf-8')

    return out_file