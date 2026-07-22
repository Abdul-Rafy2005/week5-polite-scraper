import re
import time
import logging
from urllib.parse import urlparse

import requests

logger = logging.getLogger("polite_scraper")


class RateLimitedFetcher:
    def __init__(self, config: dict, robots_checker):
        self.config = config
        self.robots = robots_checker
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config["user_agent"]})
        self.delay = config["delay"]
        self.max_retries = config["max_retries"]
        self.timeout = config["timeout"]
        self._last_request_time = 0.0
        self.visited: set[str] = set()
        self.request_log: list[dict] = []

    def fetch(self, url: str) -> requests.Response | None:
        if url in self.visited:
            logger.debug("Already visited: %s — skipping", url)
            return None

        if not self.robots.is_allowed(url):
            logger.warning("Blocked by robots.txt: %s", url)
            return None

        self._wait()

        for attempt in range(1, self.max_retries + 1):
            start = time.monotonic()
            try:
                resp = self.session.get(url, timeout=self.timeout)
                elapsed = time.monotonic() - start
                status = resp.status_code
                retried = attempt > 1

                self._log_request(url, status, elapsed, retried)

                if status == 429:
                    retry_after = float(resp.headers.get("Retry-After", 30))
                    logger.warning(
                        "429 Too Many Requests on %s — backing off %.1fs (attempt %d/%d)",
                        url, retry_after, attempt, self.max_retries,
                    )
                    time.sleep(retry_after)
                    continue

                if status >= 500:
                    backoff = 2 ** attempt
                    logger.warning(
                        "Server error %d on %s — retrying in %ds (attempt %d/%d)",
                        status, url, backoff, attempt, self.max_retries,
                    )
                    time.sleep(backoff)
                    continue

                if status == 200:
                    self.visited.add(url)
                    resp.encoding = self._detect_encoding(resp)
                    return resp

                logger.warning("HTTP %d for %s — not retrying", status, url)
                return None

            except requests.RequestException as e:
                elapsed = time.monotonic() - start
                backoff = 2 ** attempt
                logger.warning(
                    "Network error on %s: %s — retrying in %ds (attempt %d/%d)",
                    url, e, backoff, attempt, self.max_retries,
                )
                self._log_request(url, 0, elapsed, attempt > 1)
                time.sleep(backoff)

        logger.error("All %d retries exhausted for %s", self.max_retries, url)
        return None

    def _wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request_time
        effective_delay = self.delay

        # Respect robots.txt crawl-delay if stricter
        if self.robots.crawl_delay and self.robots.crawl_delay > effective_delay:
            effective_delay = self.robots.crawl_delay

        if elapsed < effective_delay:
            wait_time = effective_delay - elapsed
            logger.debug("Throttling: waiting %.2fs before next request", wait_time)
            time.sleep(wait_time)

        self._last_request_time = time.monotonic()

    def _log_request(self, url: str, status: int, elapsed: float, retried: bool) -> None:
        entry = {
            "url": url,
            "status": status,
            "response_time": round(elapsed, 3),
            "retried": retried,
        }
        self.request_log.append(entry)
        logger.info(
            "GET %s -> %d (%.3fs)%s",
            url, status, elapsed, " [RETRIED]" if retried else "",
        )

    @staticmethod
    def _detect_encoding(resp: requests.Response) -> str:
        # Check HTML meta charset first (most reliable for HTML pages)
        content_type = resp.headers.get("content-type", "")
        if "text/html" in content_type:
            head = resp.content[:4096]
            match = re.search(rb'charset=["\']?([A-Za-z0-9_-]+)', head, re.IGNORECASE)
            if match:
                return match.group(1).decode("ascii")
        # Fall back to apparent_encoding, then raw encoding
        return resp.apparent_encoding or resp.encoding
