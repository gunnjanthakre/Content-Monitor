# Content Monitoring & Flagging System

A Django + Django REST Framework backend that ingests content, scores keyword matches, and supports a human review workflow with suppression logic.

---

## Stack
- Python 3.13
- Django 6.0
- Django REST Framework 3.17
- SQLite

---

## Setup
```bash
# 1. Clone the repo
git clone https://github.com/gunnjanthakre/Content-Monitor.git
cd Content-Monitor

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Start the server
python manage.py runserver
```

Server runs at `http://127.0.0.1:8000`

---

## Content Source

Uses a **mock dataset** of 6 articles defined in `services/sources.py`.  
Topics covered: Django, Python, automation, data pipelines, machine learning.  
Adding a real API source only requires a new loader function in `sources.py` — nothing else changes.

---

## API Endpoints

### POST `/keywords/` — Create a keyword
```bash
curl -s -X POST http://127.0.0.1:8000/keywords/ \
  -H "Content-Type: application/json" \
  -d '{"name": "django"}'
```

Seed all example keywords:
```bash
for kw in django python automation "data pipeline"; do
  curl -s -X POST http://127.0.0.1:8000/keywords/ \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"$kw\"}"
  echo
done
```

### GET `/keywords/` — List all keywords
```bash
curl -s http://127.0.0.1:8000/keywords/
```

### POST `/scan/` — Trigger a scan
```bash
curl -s -X POST http://127.0.0.1:8000/scan/ \
  -H "Content-Type: application/json" \
  -d '{"source": "mock"}'
```

Response:
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

### GET `/flags/` — List all flags
```bash
curl -s http://127.0.0.1:8000/flags/
curl -s "http://127.0.0.1:8000/flags/?status=pending"
curl -s "http://127.0.0.1:8000/flags/?status=irrelevant"
```

### PATCH `/flags/{id}/` — Update review status
```bash
# Mark relevant
curl -s -X PATCH http://127.0.0.1:8000/flags/1/ \
  -H "Content-Type: application/json" \
  -d '{"status": "relevant"}'

# Mark irrelevant (triggers suppression)
curl -s -X PATCH http://127.0.0.1:8000/flags/1/ \
  -H "Content-Type: application/json" \
  -d '{"status": "irrelevant"}'
```

---

## Scoring Rules

| Condition | Score |
|---|---|
| Keyword is exact whole-word match in title | 100 |
| Keyword appears as substring in title | 70 |
| Keyword appears only in body | 40 |
| No match | 0 — no flag created |

Implemented in `services/matching.py` as pure Python with no ORM dependency.

---

## Suppression Logic

This is the core business rule.

When a reviewer marks a flag **irrelevant**:
1. `Flag.suppressed_at_content_version` is set to the content item's `last_updated` at that moment
2. On the next scan, `ScanService._upsert_flag()` calls `flag.is_suppressed_for(item.last_updated)`
3. If timestamps **match** → content unchanged → flag stays suppressed → `skipped`
4. If timestamps **differ** → content changed → flag resets to `pending` → `updated`
```python
# flags/models.py
def is_suppressed_for(self, content_last_updated) -> bool:
    if self.status != self.Status.IRRELEVANT:
        return False
    return self.suppressed_at_content_version == content_last_updated
```

### Demo the suppression cycle
```bash
# 1. Create keyword and scan
curl -s -X POST http://127.0.0.1:8000/keywords/ -H "Content-Type: application/json" -d '{"name": "django"}'
curl -s -X POST http://127.0.0.1:8000/scan/ -H "Content-Type: application/json" -d '{"source": "mock"}'

# 2. Mark flag irrelevant
curl -s -X PATCH http://127.0.0.1:8000/flags/1/ -H "Content-Type: application/json" -d '{"status": "irrelevant"}'

# 3. Re-scan — flag stays suppressed
curl -s -X POST http://127.0.0.1:8000/scan/ -H "Content-Type: application/json" -d '{"source": "mock"}'
# → flags_skipped_suppressed: 1

# 4. Simulate content update
python manage.py shell -c "
from content.models import ContentItem
from django.utils.timezone import now
item = ContentItem.objects.first()
item.last_updated = now()
item.save()
"

# 5. Re-scan — flag is reactivated
curl -s -X POST http://127.0.0.1:8000/scan/ -H "Content-Type: application/json" -d '{"source": "mock"}'
# → flags_updated: 1
```

---

## Running Tests
```bash
# Integration + API tests
python manage.py test tests.test_scan -v 2

# Pure unit tests for scoring logic
python -m unittest tests.test_matching -v
```

**17 tests, all passing.**

---

## Project Structure
```
content_monitor/
├── config/             # Settings and root URL routing
├── keywords/           # Keyword model + POST /keywords/ endpoint
├── content/            # ContentItem model
├── flags/              # Flag model, suppression logic, review API
├── services/
│   ├── matching.py     # Pure scoring logic — no ORM
│   ├── scan.py         # ScanService — orchestrates everything
│   └── sources.py      # Mock article loader
└── tests/              # 17 automated tests
```

---

## Assumptions & Trade-offs

**Mock data over real API** — keeps the project self-contained with no API keys needed. Adding a real feed only requires a new function in `sources.py`.

**`external_id` on ContentItem** — the assignment doesn't specify how to identify content items across scans. I derive a stable ID from `source + title` for mock data. A real API would supply a URL or native ID.

**Suppression uses timestamp comparison** — storing `suppressed_at_content_version` and comparing it against `ContentItem.last_updated` on each scan is exact, lightweight, and requires no extra hashing.

**One flag per (keyword, content_item) pair** — enforced via `unique_together`. Re-scanning updates the score in place rather than creating duplicates.

**Score is read-only for reviewers** — only `status` is writable via PATCH. Scores are recomputed automatically on scan to prevent data corruption.

**No authentication** — out of scope. Production would require auth on the review endpoints.