import argparse
import sys

from rich.console import Console

from config_loader import load_config
from feed_reader import fetch_all_feeds
from content_extractor import extract_contents
from organizer import organize
from llm_summarizer import summarize_clusters
from ranker import rank_news
from renderer import render_html
from telegram_sender import send_to_telegram

console = Console()

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description='Automatic Summaries and Customable RSS Feed')
    p.add_argument('-c', '--config', default='config.yml', 
                   help='Path of config file in YAML')
    p.add_argument('-m', '--llm-model', default='', 
                   help='LLM model to use for summarization')
    p.add_argument('-a', '--api-key', default='', 
                   help='LLM api key')
    p.add_argument('-u', '--url', default='', 
                   help='URL of your model provider')
    p.add_argument('--hours-lookback', default='', 
                   help='How many hours going back (0 = all)')
    p.add_argument('--max-articles', default='', 
                   help='How many articles per feed (0 = all)')
    p.add_argument('-w', '--max-workers', default='', 
                   help='Parallelization workers')
    p.add_argument('-o', '--output-dir', 
                   default='', help='Output directory where to save the output HTML')
    return p.parse_args()

def main():
    args = parse_args()

    # *** STEP 1: Configuration *************************
    console.print('[bold cyan]RSS Dietician[/bold cyan]')
    console.print(f'[dim]Reading config file: {args.config}[/dim]')
    try:
        config = load_config(args)
    except (FileNotFoundError, ValueError) as e:
        console.print(f'[bold red]Error config:[/bold red] {e}')
        sys.exit(1)

    console.print(f'    Feed loaded:  '  
                  f'[bold]{len(config.feeds)}[/bold]')
    console.print(f'    LLM provider:        '
                  f'[bold]{config.llm.model} / {config.llm.base_url}[/bold]')
    console.print(f'    Lookback:            '
                  f'[bold]{config.hours_lookback}h[/bold]')
    console.print(f'    Max articles:        '
                  f'[bold]{config.max_articles_per_feed}[/bold]')
    console.print(f'    Max workers:         '
                  f'[bold]{config.max_workers}[/bold]')
    console.print(f'    Output:              '
                  f'[bold]{config.output_dir}[/bold]')

    # *** STEP 2: Feed Retrieval ************************
    console.print('[purple]1 / 5    Reading RSS feeds[/purple]')
    articles = fetch_all_feeds(config)
    if not articles:
        console.print(f'[yellow]No articles found. '
                      f'Please revise your feeds in {args.config}.[/yellow]')
        sys.exit(0)
    console.print(f'    Articles found: [bold]{len(articles)}[/bold]')

    # *** STEP 3: Extracting Content ********************
    console.print('[purple]2 / 5    Extracting content[/purple]')
    articles, n_articles_with_content = extract_contents(articles, 
                                              max_workers=config.max_workers)
    console.print(f'    Articles extracted: [bold]{n_articles_with_content}[/bold]')

    # *** STEP 4: Organizing and clustering results *****
    console.print('[purple]3 / 5    Clustering News[/purple]')
    clusters = organize(articles)
    console.print(f'    News: [bold]{len(clusters)}[/bold] | '
                  f'Articles: {sum(len(c.articles) for c in clusters)}')

    # *** STEP 5: Summarizing ***************************
    if config.llm.api_key_env:
        console.print('[purple]4 / 5    Summarizing Articles[/purple]')
        newspaper = summarize_clusters(clusters, config.llm)
    else:
        console.print(
            f'[yellow]⚠ API key not found '
            f'(variable {config.llm.api_key_env}). '
            f'Skipping LLM summaries.[/yellow]'
        )
        newspaper = {}
        for c in clusters:
            newspaper[c.id] = {
                'title': c.articles[0].title, 
                'summary': '',
                'articles': c.articles
            }

    # *** STEP 6: Ranking News ********************
    console.print('[purple]5 / 5    Ranking news[/purple]')
    newspaper = rank_news(newspaper)
        
    # *** STEP 7: Presenting Results ********************
    render_html(newspaper, 
                output_dir=config.output_dir)
    console.print('[green]Your RSS diet is served![/green]')

    # *** STEP 8: Send to Telegram *********************
    tg_token = config.telegram.bot_token
    tg_chat = config.telegram.chat_id
    
    if tg_token and tg_chat:
        send_to_telegram(tg_token, tg_chat, config.output_dir)
        console.print("    Sent to Telegram")
    else:
        console.print("    [dim]Telegram not configured, skipping.[/dim]")

if __name__ == '__main__':
    main()