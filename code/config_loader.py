import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

import yaml

load_dotenv()

@dataclass
class LLMConfig:
    model: str = 'model-to-use'
    api_key_env: str = 'your-api-key'
    base_url: str = 'your-model-provider-url'

    @property
    def api_key(self) -> Optional[str]:
        return os.environ.get(self.api_key_env)

@dataclass
class OutputConfig:
    dir: str ='output'

@dataclass
class FeedConfig:
    url: str

@dataclass
class TelegramConfig:
    bot_token: str 
    chat_id: str

@dataclass
class AppConfig:
    llm: LLMConfig
    feeds: List[FeedConfig]
    telegram: TelegramConfig
    output_dir: str = ''
    hours_lookback: int = 0
    max_articles_per_feed: int = 0
    max_workers: int = 0

def load_config(args) -> AppConfig:
    path = Path(args.config)
    if not path.exists():
        raise FileNotFoundError(f'config YAML file not found in: {path.resolve()}')

    with open(path,'r', encoding='utf-8') as f:
        raw = yaml.safe_load(f)

    llm_raw = raw.get('llm', {})
    llm = LLMConfig(
        model = (args.llm_model
                 or os.getenv('LLM_MODEL', llm_raw.get('model'))),
        api_key_env = (args.api_key 
                       or os.getenv('LLM_API_KEY', llm_raw.get('api_key'))),
        base_url = (args.url 
                    or os.getenv('LLM_URL', llm_raw.get('base_url'))),
    )

    feeds = [
        FeedConfig(f)
        for f in raw.get('feeds', [])
    ]
    if not feeds:
        raise ValueError('No feed provided in config.yml')

    telegram_raw = raw.get('telegram', {})
    telegram = TelegramConfig(
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN', telegram_raw.get('bot_token')),
        chat_id = os.getenv('TELEGRAM_CHAT_ID', telegram_raw.get('chat_id'))
    ) 

    return AppConfig(
        llm=llm,
        feeds=feeds,
         telegram=telegram,
        output_dir=str(args.output_dir 
                       or raw.get('output_dir', './newspaper')),
        hours_lookback=int(args.hours_lookback 
                           or raw.get('hours_lookback', 0)),
        max_articles_per_feed=int(args.max_articles 
                                  or raw.get('max_articles_per_feed', 0)),
        max_workers=int(args.max_workers 
                        or raw.get('max_workers', 0)),
    )
