import logging
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

def send_to_telegram(bot_token: str, chat_id: str, output_dir: str):   
    html_files = list(Path(output_dir).glob("*.html"))
    if not html_files:
        logger.warning("[yellow]No HTML file found to send.[/yellow]")
        return

    html_path = sorted(html_files)[-1]  # most recent
    
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    
    with open(html_path, "rb") as f:
        response = requests.post(url, data={
            "chat_id": chat_id,
            "caption": "Your RSS Diet is served!",
        }, files={
            "document": (html_path.name, f, "text/html")
        })

    if response.status_code == 200:
        logger.info("[green]RSS Diet sent on Telegram![/green]")
    else:
        logger.error(f"[red]Error Telegram: {response.text}[/red]")