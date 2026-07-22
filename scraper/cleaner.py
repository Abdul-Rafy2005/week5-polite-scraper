import logging
import re
import html

logger = logging.getLogger("polite_scraper")

STAR_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


def clean_records(records: list[dict]) -> list[dict]:
    cleaned = []
    seen_urls: set[str] = set()

    for rec in records:
        url = rec.get("url", "")
        if url in seen_urls:
            logger.debug("Duplicate URL skipped: %s", url)
            continue
        seen_urls.add(url)

        cleaned.append(_clean_one(rec))

    logger.info("Cleaned %d records (%d duplicates removed)", len(cleaned), len(records) - len(cleaned))
    return cleaned


def _clean_one(rec: dict) -> dict:
    out = dict(rec)

    # Strip + decode HTML entities on text fields
    for field in ("title", "availability_raw", "category"):
        val = out.get(field)
        if val:
            val = html.unescape(val).strip()
            out[field] = val

    # Price: strip currency symbol and convert to float
    price_raw = out.get("price_raw", "")
    if price_raw:
        price_clean = re.sub(r"[^\d.]", "", price_raw)
        try:
            out["price"] = float(price_clean)
        except (ValueError, TypeError):
            out["price"] = None
            logger.warning("Could not parse price: %s", price_raw)
    else:
        out["price"] = None

    # Star rating word to int
    rating_word = out.get("star_rating")
    if rating_word:
        out["star_rating"] = STAR_MAP.get(rating_word)
        if out["star_rating"] is None:
            logger.warning("Unknown star rating word: %s", rating_word)

    # Availability normalization
    avail = out.get("availability_raw", "")
    avail_lower = avail.lower()
    out["in_stock"] = "in stock" in avail_lower
    count_match = re.search(r"\((\d+) available\)", avail)
    out["stock_count"] = int(count_match.group(1)) if count_match else None

    # Strip description
    desc = out.get("description")
    if desc:
        desc = html.unescape(desc).strip()
        # Remove trailing "...more" or "…more" (unicode ellipsis) and variants
        desc = re.sub(r"\s*(?:\.\.\.|\u2026)\s*more\s*$", "", desc)
        out["description"] = desc

    return out
