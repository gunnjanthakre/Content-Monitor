# Content Monitoring & Flagging System

A Django + DRF backend that ingests content, scores keyword matches, and supports a human review workflow with suppression logic.

---

## Stack

- Python 3.10+
- Django 4.2
- Django REST Framework 3.14
- SQLite (default)

---

## Setup

```bash
# 1. Clone and enter the project
git clone <your-repo-url>
cd content_monitor

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. (Optional) Create a superuser for Django admin
python manage.py createsuperuser

# 6. Start the dev server
python manage.py runserver
```

The server runs at `http://127.0.0.1:8000`.
Django admin is available at `http://127.0.0.1:8000/admin/`.

---

## Running Tests

```bash
# Integration + API tests (requires Django)
python manage.py test tests.test_scan -v 2

# Pure unit tests for matching logic (no Django needed)
python -m unittest tests.test_matching -v
```

---

## Content Source

This implementation uses a **mock dataset** (defined in `services/sources.py`).

The mock contains 6 articles covering topics like Django, Python, automation, and data pipelines — enough to produce meaningful flags for the example keywords listed in the assignment.

Adding a real API source (e.g. NewsAPI, RSS) means adding a new loader function in `services/sources.py` and registering the source name in `ScanService._fetch_records()` and `ScanView`. No other changes are needed.

---

## API Reference

### POST `/keywords/` — Create a keyword

```bash
curl -s -X POST http://127.0.0.1:8000/keywords/ \
  -H "Content-Type: application/json" \
  -d '{"name": "django"}' | python -m json.tool
```

Seed all example keywords at once:

```bash
for kw in django python automation "data pipeline"; do
  curl -s -X POST http://127.0.0.1:8000/keywords/ \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"$kw\"}"
  echo
done
```

**Response (201):**
```json
{
  "id": 1,
  "name": "django",
  "created_at": "2026-03-24T10:00:00Z"
}
```

---

### GET `/keywords/` — List all keywords

```bash
curl -s http://127.0.0.1:8000/keywords/ | python -m json.tool
```

---

### POST `/scan/` — Trigger a scan

```bash
curl -s -X POST http://127.0.0.1:8000/scan/ \
  -H "Content-Type: application/json" \
  -d '{"source": "mock"}' | python -m json.tool
```

**Response (200):**
```json
{
  "source": "mock",
  "content_items_processed": 6,
  "keywords_active": 4,
  "flags_created": 8,
  "flags_updated": 0,
  "flags_skipped_suppressed": 0
}
```

Running the scan again produces no new flags (idempotent):
```json
{
  "flags_created": 0,
  "flags_updated": 0,
  "flags_skipped_suppressed": 8
}
```

---

### GET `/flags/` — List all flags

```bash
curl -s http://127.0.0.1:8000/flags/ | python -m json.tool
```

Filter by status:

```bash
curl -s "http://127.0.0.1:8000/flags/?status=pending" | python -m json.tool
curl -s "http://127.0.0.1:8000/flags/?status=relevant" | python -m json.tool
curl -s "http://127.0.0.1:8000/flags/?status=irrelevant" | python -m json.tool
```

**Response example:**
```json
[
  {
    "id": 1,
    "keyword": 1,
    "keyword_name": "django",
    "content_item": 1,
    "content_title": "Learn Django Fast",
    "content_source": "mock",
    "score": 100,
    "status": "pending",
    "suppressed_at_content_version": null,
    "created_at": "2026-03-24T10:00:00Z",
    "updated_at": "2026-03-24T10:00:00Z"
  }
]
```

---

### GET `/flags/{id}/` — Retrieve a single flag

```bash
curl -s http://127.0.0.1:8000/flags/1/ | python -m json.tool
```

---

### PATCH `/flags/{id}/` — Update review status

Mark as **relevant**:
```bash
curl -s -X PATCH http://127.0.0.1:8000/flags/1/ \
  -H "Content-Type: application/json" \
  -d '{"status": "relevant"}' | python -m json.tool
```

Mark as **irrelevant** (triggers suppression):
```bash
curl -s -X PATCH http://127.0.0.1:8000/flags/1/ \
  -H "Content-Type: application/json" \
  -d '{"status": "irrelevant"}' | python -m json.tool
```

Reset to **pending**:
```bash
curl -s -X PATCH http://127.0.0.1:8000/flags/1/ \
  -H "Content-Type: application/json" \
  -d '{"status": "pending"}' | python -m json.tool
```

---

## Suppression Logic

This is the core business rule. When a reviewer marks a flag **irrelevant**:

1. The flag's `suppressed_at_content_version` is set to the content item's `last_updated` at that moment.
2. On the **next scan**, `ScanService._upsert_flag()` calls `flag.is_suppressed_for(item.last_updated)`.
3. If `suppressed_at_content_version == item.last_updated` → content **unchanged** → flag stays suppressed (`skipped`).
4. If they **differ** → content changed → flag is reset to `pending` with the new score (`updated`).

### Simulating a suppression + content-change cycle

```bash
# 1. Seed keywords and run first scan
curl -s -X POST http://127.0.0.1:8000/keywords/ -H "Content-Type: application/json" -d '{"name": "django"}'
curl -s -X POST http://127.0.0.1:8000/scan/ -H "Content-Type: application/json" -d '{"source": "mock"}'

# 2. Mark flag #1 as irrelevant
curl -s -X PATCH http://127.0.0.1:8000/flags/1/ -H "Content-Type: application/json" -d '{"status": "irrelevant"}'

# 3. Re-scan — flag stays suppressed
curl -s -X POST http://127.0.0.1:8000/scan/ -H "Content-Type: application/json" -d '{"source": "mock"}'
# → flags_skipped_suppressed: 1

# 4. Simulate content change: update last_updated in the DB (Django shell)
python manage.py shell -c "
from content.models import ContentItem
from django.utils.timezone import now
item = ContentItem.objects.first()
item.last_updated = now()
item.save()
print('Updated:', item)
"

# 5. Re-scan — flag is now reactivated
curl -s -X POST http://127.0.0.1:8000/scan/ -H "Content-Type: application/json" -d '{"source": "mock"}'
# → flags_updated: 1
```

---

## Scoring Rules

| Condition | Score |
|---|---|
| Keyword is an exact whole-word match in `title` | 100 |
| Keyword appears as a substring in `title` | 70 |
| Keyword appears only in `body` | 40 |
| No match | 0 (no flag created) |

"Exact" means the keyword is surrounded by non-alphanumeric characters or string boundaries — so `python` is an exact match in `"Python 3 Guide"` but not in `"Pythons in the wild"`.

---

## Project Structure

```
content_monitor/
├── manage.py
├── requirements.txt
├── README.md
├── config/
│   ├── settings.py
│   └── urls.py
├── keywords/
│   ├── models.py        # Keyword model
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── content/
│   └── models.py        # ContentItem model
├── flags/
│   ├── models.py        # Flag model + suppression methods
│   ├── serializers.py
│   ├── views.py         # FlagListView, FlagDetailView
│   ├── scan_view.py     # ScanView
│   ├── urls.py
│   └── scan_urls.py
├── services/
│   ├── matching.py      # Pure scoring logic (no ORM)
│   ├── scan.py          # ScanService (orchestration)
│   └── sources.py       # Content loaders (mock / future APIs)
└── tests/
    ├── test_matching.py  # Pure unit tests
    └── test_scan.py      # Integration + API tests
```

---

## Assumptions & Trade-offs

**Mock data over real API**: The assignment explicitly permits a mock dataset. Using mock data keeps the project self-contained (no API keys needed) and makes the suppression cycle reproducible. Integrating a real feed (e.g. NewsAPI) would require only a new function in `sources.py`.

**`external_id` on ContentItem**: The assignment doesn't specify how to identify content items across scans. I added an `external_id` field (derived from `source + title` for mock data; a real API would provide a URL or native ID). This is what makes reliable upsert and suppression tracking possible.

**Suppression uses `last_updated` timestamp comparison**: The assignment says to treat `last_updated` as the change signal. I store a snapshot of that timestamp when a flag is suppressed (`suppressed_at_content_version`) and compare it on the next scan. This is exact and requires no extra hashing.

**One flag per (keyword, content_item) pair**: Enforced via `unique_together`. Re-scanning updates the score in place rather than creating new rows. This keeps the review history clean.

**Score is immutable from reviewer's perspective**: Only the `status` field is writable via the PATCH endpoint. Scores are recomputed automatically on scan. This prevents reviewers from accidentally corrupting match data.

**No authentication**: Out of scope for this assignment. In production, the review endpoints would require auth/permissions.

**SQLite**: Sufficient for a local assignment. Switching to Postgres requires only changing the `DATABASES` setting.