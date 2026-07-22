from scraper.config import load_config
from scraper.logging_config import setup_logging


def main():
    cfg = load_config()
    logger = setup_logging(cfg["log_file"])
    logger.info("Scraper initialized with config: %s", cfg)
    logger.info("Nothing to do yet — this is the Stage 0 scaffold.")


if __name__ == "__main__":
    main()
