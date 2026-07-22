import csv
import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger("polite_scraper")

CSV_FIELDS = [
    "url",
    "title",
    "price",
    "price_raw",
    "availability_raw",
    "in_stock",
    "stock_count",
    "star_rating",
    "category",
    "image_url",
    "description",
]


def save_json(records: list[dict], path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    logger.info("Saved %d records to %s", len(records), path)


def save_csv(records: list[dict], path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            row = {k: rec.get(k) for k in CSV_FIELDS}
            writer.writerow(row)
    logger.info("Saved %d records to %s", len(records), path)


def save_run_metadata(
    path: str,
    pages_fetched: int,
    records_extracted: int,
    robots_summary: dict,
    duration: float,
    request_log: list[dict],
) -> None:
    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_pages_fetched": pages_fetched,
        "total_records_extracted": records_extracted,
        "robots_txt_restrictions": robots_summary,
        "total_run_duration_seconds": round(duration, 2),
        "total_requests": len(request_log),
        "retried_requests": sum(1 for r in request_log if r.get("retried")),
    }
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    logger.info("Saved run metadata to %s", path)
