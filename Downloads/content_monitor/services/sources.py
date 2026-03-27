import hashlib
from datetime import datetime, timezone


MOCK_ARTICLES = [
    {
        "title": "Learn Django Fast",
        "body": "Django is a powerful Python web framework used for rapid development.",
        "source": "mock",
        "last_updated": "2026-03-20T10:00:00Z",
    },
    {
        "title": "Cooking Tips for Beginners",
        "body": "Best recipes for beginners who love baking.",
        "source": "mock",
        "last_updated": "2026-03-20T10:00:00Z",
    },
    {
        "title": "Python Automation Scripts",
        "body": "Automate repetitive tasks using Python and shell scripts.",
        "source": "mock",
        "last_updated": "2026-03-21T08:00:00Z",
    },
    {
        "title": "Building a Data Pipeline",
        "body": "A practical guide to building robust data pipeline architectures.",
        "source": "mock",
        "last_updated": "2026-03-21T09:00:00Z",
    },
    {
        "title": "Intro to Machine Learning",
        "body": "This article covers supervised and unsupervised learning techniques.",
        "source": "mock",
        "last_updated": "2026-03-22T07:30:00Z",
    },
    {
        "title": "Django REST Framework Tutorial",
        "body": "Build APIs quickly using Django REST Framework and Python.",
        "source": "mock",
        "last_updated": "2026-03-22T12:00:00Z",
    },
]


def _stable_id(source: str, title: str) -> str:
    raw = f"{source}::{title}".encode()
    return hashlib.sha1(raw).hexdigest()


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def fetch_mock() -> list[dict]:
    records = []
    for item in MOCK_ARTICLES:
        records.append({
            "title": item["title"],
            "body": item["body"],
            "source": item["source"],
            "last_updated": _parse_dt(item["last_updated"]),
            "external_id": _stable_id(item["source"], item["title"]),
        })
    return records