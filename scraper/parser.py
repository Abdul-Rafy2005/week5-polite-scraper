import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup

logger = logging.getLogger("polite_scraper")


def parse_product_page(html: str, url: str, base_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    record = {
        "url": url,
        "title": None,
        "price_raw": None,
        "availability_raw": None,
        "star_rating": None,
        "category": None,
        "image_url": None,
        "description": None,
    }

    # Title
    h1 = soup.select_one("h1")
    if h1:
        record["title"] = h1.get_text(strip=True)
    else:
        logger.warning("No title found for %s", url)

    # Price
    price_el = soup.select_one("p.price_color")
    if price_el:
        record["price_raw"] = price_el.get_text(strip=True)
    else:
        logger.warning("No price found for %s", url)

    # Availability
    avail_el = soup.select_one("p.instock.availability")
    if avail_el:
        record["availability_raw"] = avail_el.get_text(strip=True)
    else:
        logger.warning("No availability found for %s", url)

    # Star rating
    star_el = soup.select_one("p.star-rating")
    if star_el:
        classes = star_el.get("class", [])
        for cls in classes:
            if cls.lower() != "star-rating":
                record["star_rating"] = cls
                break
    if not record["star_rating"]:
        logger.warning("No star rating found for %s", url)

    # Category (from breadcrumb, skip "Home" and "Books")
    breadcrumb = soup.select("ul.breadcrumb li")
    for li in breadcrumb:
        a = li.select_one("a")
        if a and a.get_text(strip=True) not in ("Home", "Books", ""):
            record["category"] = a.get_text(strip=True)
            break

    # Image
    img = soup.select_one("#product_gallery img")
    if img and img.get("src"):
        record["image_url"] = urljoin(base_url + "/", img["src"])
    else:
        logger.warning("No image found for %s", url)

    # Description
    desc_div = soup.select_one("#product_description")
    if desc_div:
        p = desc_div.find_next_sibling("p")
        if p:
            record["description"] = p.get_text(strip=True)
    if not record["description"]:
        # Try meta description
        meta = soup.select_one('meta[name="description"]')
        if meta and meta.get("content"):
            record["description"] = meta["content"].strip()

    return record
