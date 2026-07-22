import logging
from scraper.config import load_config
from scraper.logging_config import setup_logging
from scraper.robots import RobotsChecker
from scraper.fetcher import RateLimitedFetcher
from scraper.collector import Collector
from scraper.parser import parse_product_page
from scraper.cleaner import clean_records

logger = logging.getLogger("polite_scraper")


def main():
    cfg = load_config()
    logger = setup_logging(cfg["log_file"])
    logger.info("Scraper initialized with config: %s", cfg)

    robots = RobotsChecker(cfg["base_url"], cfg["user_agent"])
    robots.fetch()

    fetcher = RateLimitedFetcher(cfg, robots)
    collector = Collector(cfg["base_url"], fetcher)
    product_urls = collector.crawl(max_pages=cfg["max_pages"])
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

    for r in cleaned[:3]:
        logger.info("  Sample: %s", r)


if __name__ == "__main__":
    main()
