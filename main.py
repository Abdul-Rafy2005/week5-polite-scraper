from scraper.config import load_config
from scraper.logging_config import setup_logging
from scraper.robots import RobotsChecker
from scraper.fetcher import RateLimitedFetcher


def main():
    cfg = load_config()
    logger = setup_logging(cfg["log_file"])
    logger.info("Scraper initialized with config: %s", cfg)

    robots = RobotsChecker(cfg["base_url"], cfg["user_agent"])
    robots.fetch()

    summary = robots.get_restriction_summary()
    logger.info("robots.txt summary: %s", summary)

    fetcher = RateLimitedFetcher(cfg, robots)
    resp = fetcher.fetch(cfg["base_url"])
    if resp:
        logger.info("Fetched homepage: %d", resp.status_code)
    else:
        logger.error("Failed to fetch homepage")


if __name__ == "__main__":
    main()
