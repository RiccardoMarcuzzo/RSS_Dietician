import logging
import re
from typing import List, Tuple, Dict

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

from config_loader import LLMConfig
from organizer import Cluster
from feed_reader import Article

logger = logging.getLogger(__name__)

def load_models(cfg: LLMConfig) -> Tuple:
    refiner_llm = ChatOpenAI(
        model=cfg.model,
        api_key=cfg.api_key_env,
        base_url=cfg.base_url,
        temperature=0
    )
    journalist_llm = ChatOpenAI(
        model=cfg.model,
        api_key=cfg.api_key_env,
        base_url=cfg.base_url,
        temperature=0.45, top_p=0.85
    )
    headliner_llm = ChatOpenAI(
        model=cfg.model,
        api_key=cfg.api_key_env,
        base_url=cfg.base_url,
        temperature=0.9, top_p=0.95
    )

    return refiner_llm, journalist_llm, headliner_llm

refiner_prompt = ChatPromptTemplate.from_messages([
    ('system', """
    You are an helpful news assistant. Your task is to read a set of articles 
    and group those that cover the same news story.
    Instructions:
    - Identify articles that report on the same underlying news story or narrative.
    - Keep articles together in the same group when they pertain to the same narrative. Avoid creating many small fragmented groups.
    - Every article index must appear in exactly one group. Use the exact indices shown in square brackets.
    - Respond ONLY with valid JSON, with no extra text, in the following format:
    {{
    "news_1": {{"articles": [<article indices>]}},
    "news_2": {{"articles": [<article indices>]}}
    }}"""),
    
    ('human', 'ARTICLES:\n{articles}')
])

journalist_prompt = ChatPromptTemplate.from_messages([
    ('system', """
    You are a journalist assistant. Given the following group of articles covering the same news story, write a concise, engaging summary.
    Instructions:
    - Stay strictly grounded in the provided articles; do not invent facts, names, numbers, or quotes not present in the source material.
    - Write in a clear, inviting prose style suitable for a news digest.
    - If the articles present different perspectives or viewpoints, highlight them.
    - Be concise but cover every relevant aspect. Write between 150 and 300 words."""),
    
    ('human', 'ARTICLES:\n{articles}')
])

headliner_prompt = ChatPromptTemplate.from_messages([
    ('system', """
    You are a creative news headline writer. Given a news summary, write a single compelling, accurate headline.
    - Be faithful to the facts in the summary.
    - Be engaging and natural, as a skilled journalist would write.
    - Output ONLY the headline text, no quotes, no extra commentary."""),

    ('human', 'SUMMARY:\n{summary}')
])

def _format_articles(articles: List[Article]) -> str:
    return '\n\n'.join(
        f'[{i}] {a.title}\n{a.content}' for i, a in enumerate(articles)
    )

def summarize_clusters(clusters: List[Cluster], cfg: LLMConfig) -> Dict[int, Dict]:
    newspaper = {}
    current_news = 0
    refiner_llm, journalist_llm, headliner_llm = load_models(cfg)
    refiner_chain    = refiner_prompt    | refiner_llm    | JsonOutputParser()
    journalist_chain = journalist_prompt | journalist_llm | StrOutputParser()
    headliner_chain  = headliner_prompt  | headliner_llm  | StrOutputParser()

    estimated_steps = sum(1 + 2 for _ in clusters)
    with Progress(
        SpinnerColumn(),
        TextColumn('[bold cyan]{task.description}'),
        BarColumn(),
        TaskProgressColumn(),
        transient=True,
    ) as progress:
        task = progress.add_task('Cluster analysis...', total=estimated_steps)

        for c in clusters:
            if len(c.articles) > 3:
                progress.update(task, description=f'Refining cluster ({len(c.articles)} articles)...')
                sub_clusters = refiner_chain.invoke({'articles': _format_articles(c.articles)})

                n = len(c.articles)
                valid = all(
                    isinstance(i, int) and 0 <= i < n
                    for v in sub_clusters.values()
                    for i in v['articles']
                )
                if not valid:
                    logger.warning('Refiner returned invalid indices, falling back to full cluster.')
                    sub_clusters_list = [c.articles]
                else:
                    sub_clusters_list = [
                        [c.articles[i] for i in v['articles']]
                        for v in sub_clusters.values()
                    ]
            else:
                sub_clusters_list = [c.articles]

            progress.advance(task)

            for articles in sub_clusters_list:
                current_news += 1

                progress.update(task, description=f'Writing news {current_news}...')
                summary = journalist_chain.invoke({'articles': _format_articles(articles)})
                summary = re.sub(r'^summary\s*[::\-–—]?\s*', '', summary, 
                                 flags=re.IGNORECASE).strip()
                summary = summary.strip('"')
                progress.advance(task)

                progress.update(task, description=f'Headlining news {current_news}...')
                title = headliner_chain.invoke({'summary': summary})
                title = re.sub(r'^headline\s*[::\-–—]?\s*', '', title, 
                               flags=re.IGNORECASE).strip()
                title = title.strip('"')
                progress.advance(task)

                newspaper[current_news] = {
                    'title': title,
                    'summary': summary,
                    'articles': articles,
                }

    return newspaper
