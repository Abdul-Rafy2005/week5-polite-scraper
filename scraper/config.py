import yaml
from pathlib import Path

DEFAULTS = {
    "base_url": "https://books.toscrape.com",
    "delay": 1.5,
    "max_pages": 20,
    "max_retries": 3,
    "user_agent": "PoliteScraperBot/1.0 (+educational project; contact: you@example.com)",
    "output_json": "data/books.json",
    "output_csv": "data/books.csv",
    "log_file": "scraper.log",
    "timeout": 10,
}


def load_config(path: str = "config.yaml") -> dict:
    cfg = dict(DEFAULTS)
    p = Path(path)
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            user_cfg = yaml.safe_load(f) or {}
        cfg.update(user_cfg)
    return cfg
