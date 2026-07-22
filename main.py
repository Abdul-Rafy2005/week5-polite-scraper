from scraper.config import load_config
from scraper.logging_config import setup_logging
from scraper.robots import RobotsChecker
from scraper.fetcher import RateLimitedFetcher
from scraper.collector import Collector


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
    for i, url in enumerate(product_urls[:5], 1):
        logger.info("  %d. %s", i, url)


if __name__ == "__main__":
    main()
