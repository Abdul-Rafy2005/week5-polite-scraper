import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup

logger = logging.getLogger("polite_scraper")


class Collector:
    def __init__(self, base_url: str, fetcher):
        self.base_url = base_url
        self.fetcher = fetcher
        self.product_urls: list[str] = []

    def crawl(self, max_pages: int) -> list[str]:
        url = self.base_url
        pages_fetched = 0

        while url and pages_fetched < max_pages:
            logger.info("Crawling page %d: %s", pages_fetched + 1, url)
            resp = self.fetcher.fetch(url)
            if resp is None:
                logger.warning("Failed to fetch listing page: %s", url)
                break

            pages_fetched += 1
            soup = BeautifulSoup(resp.text, "html.parser")

            self._extract_product_links(soup, url)
            url = self._find_next_page(soup, url)

        logger.info(
            "Crawl complete: %d listing pages fetched, %d product URLs collected",
            pages_fetched,
            len(self.product_urls),
        )
        return list(self.product_urls)

    def _extract_product_links(self, soup: BeautifulSoup, current_url: str) -> None:
        for article in soup.select("article.product_pod"):
            link = article.select_one("h3 a")
            if link and link.get("href"):
                href = link["href"]
                # Resolve relative to the current listing page URL
                full_url = urljoin(current_url, href)
                # Only follow links within books.toscrape.com
                if self.base_url in full_url:
                    if full_url not in self.fetcher.visited:
                        self.product_urls.append(full_url)

    def _find_next_page(self, soup: BeautifulSoup, current_url: str) -> str | None:
        next_btn = soup.select_one("li.next a")
        if next_btn and next_btn.get("href"):
            href = next_btn["href"]
            next_url = urljoin(current_url, href)
            return next_url
        return None
