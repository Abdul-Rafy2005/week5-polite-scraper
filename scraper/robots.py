import time
import logging
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

import requests

logger = logging.getLogger("polite_scraper")


class RobotsChecker:
    def __init__(self, base_url: str, user_agent: str):
        self.base_url = base_url
        self.user_agent = user_agent
        self.parser = RobotFileParser()
        self.crawl_delay: float | None = None
        self.restrictions: list[str] = []
        self.fetched = False

    def fetch(self) -> None:
        robots_url = urljoin(self.base_url, "/robots.txt")
        try:
            resp = requests.get(
                robots_url,
                headers={"User-Agent": self.user_agent},
                timeout=10,
            )
            if resp.status_code == 200:
                self.parser.parse(resp.text.splitlines())
                self.fetched = True
                self._extract_delay()
                self._extract_restrictions()
                logger.info(
                    "robots.txt check: fetched successfully (HTTP %d) — %s",
                    resp.status_code,
                    "restrictions honored" if self.restrictions or self.crawl_delay else "no restrictions, proceeding under default politeness settings",
                )
            else:
                logger.info(
                    "robots.txt check: not found (HTTP %d) — no restrictions, proceeding under default politeness settings",
                    resp.status_code,
                )
        except requests.RequestException as e:
            logger.info(
                "robots.txt check: fetch failed (%s) — no restrictions, proceeding under default politeness settings",
                e,
            )

    def _extract_delay(self) -> None:
        delay = self.parser.crawl_delay(self.user_agent)
        if delay is not None:
            self.crawl_delay = float(delay)
            logger.info("robots.txt Crawl-delay: %.1f seconds", self.crawl_delay)
        else:
            logger.info("No Crawl-delay directive found in robots.txt")

    def _extract_restrictions(self) -> None:
        # Check common paths for disallow
        test_paths = ["/", "/index.html", "/catalogue/", "/catalogue/page-1.html"]
        for path in test_paths:
            if not self.parser.can_fetch(self.user_agent, urljoin(self.base_url, path)):
                self.restrictions.append(path)
                logger.warning("robots.txt DISALLOWS %s for User-Agent '%s'", path, self.user_agent)
        if not self.restrictions:
            logger.info("No path restrictions found for User-Agent '%s'", self.user_agent)

    def is_allowed(self, url: str) -> bool:
        if not self.fetched:
            return True
        return self.parser.can_fetch(self.user_agent, url)

    def get_restriction_summary(self) -> dict:
        return {
            "robots_txt_fetched": self.fetched,
            "crawl_delay": self.crawl_delay,
            "disallowed_paths": list(self.restrictions),
        }
