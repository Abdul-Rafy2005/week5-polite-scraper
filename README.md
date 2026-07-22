# Polite Web Scraper

A well-behaved, rate-limited web scraper for [books.toscrape.com](https://books.toscrape.com) — built to demonstrate best practices for respectful web scraping.

## Why "Polite"?

Most scrapers blast a server with requests as fast as possible. This one is designed to behave like a good citizen:

- **Respects `robots.txt`** — before scraping, it fetches and parses the site's robots.txt file, checks whether our target paths are allowed for our User-Agent, and obeys any `Crawl-delay` directive. Check result is logged at INFO level for transparency.
- **Identifies itself** — sends a clear, honest `User-Agent` string: `PoliteScraperBot/1.0 (+educational project; contact: you@example.com)`.
- **Rate-limits requests** — enforces a configurable minimum delay between requests (default: 1.5 seconds).
- **Retries with backoff** — handles transient errors gracefully with exponential backoff; backs off further on 429 Too Many Requests.
- **Caps listing pages** — a `max_listing_pages` config prevents accidental over-crawling.

## How to Run

```bash
pip install -r requirements.txt
python main.py
```

Output is saved to `data/books.json`, `data/books.csv`, and `data/run_metadata.json`.

## Config Options

All settings live in `config.yaml` (falls back to built-in defaults if missing):

| Name | Default | Purpose |
|------|---------|---------|
| `base_url` | `https://books.toscrape.com` | Target site base URL |
| `delay` | `1.5` | Minimum seconds between requests |
| `max_listing_pages` | `20` | Max listing/category pages to crawl per run; product pages scale proportionally (~20 per listing page) and are not separately capped |
| `max_retries` | `3` | Max retries on network/5xx errors |
| `user_agent` | `PoliteScraperBot/1.0 (+educational project; contact: you@example.com)` | User-Agent header |
| `output_json` | `data/books.json` | JSON output path |
| `output_csv` | `data/books.csv` | CSV output path |
| `log_file` | `scraper.log` | Log file path |
| `timeout` | `10` | HTTP request timeout in seconds |

## Output Schema

### books.json / books.csv

| Field | Type | Example |
|-------|------|---------|
| `url` | string | `https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html` |
| `title` | string | `A Light in the Attic` |
| `price` | float | `51.77` |
| `price_raw` | string | `£51.77` |
| `availability_raw` | string | `In stock (22 available)` |
| `in_stock` | bool | `true` |
| `stock_count` | int/null | `22` |
| `star_rating` | int/null | `3` |
| `category` | string | `Poetry` |
| `image_url` | string | `https://books.toscrape.com/media/cache/fe/72/...` |
| `description` | string | `It's hard to imagine a world without...` |

### run_metadata.json

| Field | Type | Example |
|-------|------|---------|
| `timestamp` | string (ISO 8601) | `2026-07-22T18:41:47+00:00` |
| `total_pages_fetched` | int | `21` |
| `total_records_extracted` | int | `20` |
| `robots_txt_restrictions` | object | `{"robots_txt_fetched": false, ...}` |
| `total_run_duration_seconds` | float | `33.85` |
| `total_requests` | int | `21` |
| `retried_requests` | int | `0` |

## Known Limitations

- **Static HTML only** — does not execute JavaScript; works only on server-rendered pages.
- **Single-threaded** — one request at a time by design (politeness); no concurrent fetching.
- **books.toscrape.com only** — hardcoded to stay within this domain; does not follow external links.
- **No persistence across runs** — the visited set resets each run; re-crawling is expected.
- **Encoding handled** — uses HTML `<meta charset>` detection to avoid mojibake (e.g. `£` vs `┬ú`); falls back to `requests` auto-detection.

## Project Structure

```
week5-polite-scraper/
├── config.yaml              # All tunable settings
├── main.py                  # Entry point
├── requirements.txt         # Python dependencies
├── scraper/
│   ├── __init__.py
│   ├── config.py            # Config loading
│   ├── logging_config.py    # Logging setup
│   ├── robots.py            # robots.txt fetcher & parser
│   ├── fetcher.py           # Rate-limited HTTP fetcher
│   ├── collector.py         # Pagination crawler
│   ├── parser.py            # Product page extractor
│   ├── cleaner.py           # Data cleaning & normalization
│   └── output.py            # JSON/CSV/metadata output
├── data/
│   ├── books.json           # Scraped books (JSON)
│   ├── books.csv            # Scraped books (CSV)
│   └── run_metadata.json    # Run stats
└── scraper.log              # Detailed run log
```
