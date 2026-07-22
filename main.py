import time
import logging
from scraper.config import load_config
from scraper.logging_config import setup_logging
from scraper.robots import RobotsChecker
from scraper.fetcher import RateLimitedFetcher
from scraper.collector import Collector
from scraper.parser import parse_product_page
from scraper.cleaner import clean_records
from scraper.output import save_json, save_csv, save_run_metadata

logger = logging.getLogger("polite_scraper")


def main():
    cfg = load_config()
    logger = setup_logging(cfg["log_file"])
    logger.info("Scraper initialized with config: %s", cfg)

    run_start = time.monotonic()

    robots = RobotsChecker(cfg["base_url"], cfg["user_agent"])
    robots.fetch()

    fetcher = RateLimitedFetcher(cfg, robots)
    collector = Collector(cfg["base_url"], fetcher)
    product_urls = collector.crawl(max_listing_pages=cfg["max_listing_pages"])
    logger.info("Collected %d product URLs", len(product_urls))

    # Fetch and parse each product page
    raw_records = []
    for i, url in enumerate(product_urls, 1):
        logger.info("Parsing product %d/%d: %s", i, len(product_urls), url)
        resp = fetcher.fetch(url)
        if resp is None:
            logger.warning("Failed to fetch product page: %s", url)
            continue
        record = parse_product_page(resp.text, url, cfg["base_url"])
        raw_records.append(record)

    logger.info("Raw records extracted: %d", len(raw_records))

    # Clean
    cleaned = clean_records(raw_records)
    logger.info("Cleaned records: %d", len(cleaned))

    # Save output
    save_json(cleaned, cfg["output_json"])
    save_csv(cleaned, cfg["output_csv"])

    run_duration = time.monotonic() - run_start
    pages_fetched = len(fetcher.request_log)
    robots_summary = robots.get_restriction_summary()

    save_run_metadata(
        path="data/run_metadata.json",
        pages_fetched=pages_fetched,
        records_extracted=len(cleaned),
        robots_summary=robots_summary,
        duration=run_duration,
        request_log=fetcher.request_log,
    )

    logger.info(
        "Run complete: %d pages fetched, %d records extracted, %.1fs duration",
        pages_fetched, len(cleaned), run_duration,
    )


if __name__ == "__main__":
    main()
