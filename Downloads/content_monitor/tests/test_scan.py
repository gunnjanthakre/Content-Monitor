from datetime import datetime, timezone
from django.test import TestCase

from content.models import ContentItem
from flags.models import Flag
from keywords.models import Keyword
from services.scan import ScanService


def _dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def _make_item(title="Test Article", body="Some body text", source="mock",
               last_updated="2026-03-20T10:00:00Z", external_id=None) -> ContentItem:
    return ContentItem.objects.create(
        title=title, body=body, source=source,
        last_updated=_dt(last_updated),
        external_id=external_id or f"test::{title}",
    )


class TestScanService(TestCase):

    def test_scan_creates_flags(self):
        Keyword.objects.create(name="django")
        result = ScanService(source="mock").run()
        self.assertGreater(result["flags_created"], 0)

    def test_no_flags_without_keywords(self):
        result = ScanService(source="mock").run()
        self.assertEqual(result["flags_created"], 0)

    def test_no_duplicate_flags(self):
        Keyword.objects.create(name="django")
        ScanService(source="mock").run()
        count_first = Flag.objects.count()
        ScanService(source="mock").run()
        self.assertEqual(Flag.objects.count(), count_first)


class TestSuppression(TestCase):

    def setUp(self):
        self.kw = Keyword.objects.create(name="django")
        self.item = _make_item(
            title="Django REST Framework Tutorial",
            body="Build APIs with DRF",
            external_id="test::django-article",
            last_updated="2026-03-20T10:00:00Z",
        )
        self.flag = Flag.objects.create(
            keyword=self.kw, content_item=self.item,
            score=100, status=Flag.Status.PENDING,
        )

    def test_stays_suppressed_when_content_unchanged(self):
        self.flag.mark_irrelevant(self.item.last_updated)
        result = ScanService(source="mock")._upsert_flag(self.kw, self.item, score=100)
        self.assertEqual(result, "skipped")
        self.flag.refresh_from_db()
        self.assertEqual(self.flag.status, Flag.Status.IRRELEVANT)

    def test_reactivated_when_content_changes(self):
        self.flag.mark_irrelevant(self.item.last_updated)
        self.item.last_updated = _dt("2026-03-25T12:00:00Z")
        self.item.save()
        result = ScanService(source="mock")._upsert_flag(self.kw, self.item, score=100)
        self.assertEqual(result, "updated")
        self.flag.refresh_from_db()
        self.assertEqual(self.flag.status, Flag.Status.PENDING)


class TestAPIViews(TestCase):

    def test_create_keyword(self):
        r = self.client.post("/keywords/", {"name": "python"}, content_type="application/json")
        self.assertEqual(r.status_code, 201)

    def test_list_flags_empty(self):
        r = self.client.get("/flags/")
        self.assertEqual(r.status_code, 200)

    def test_patch_flag_to_irrelevant(self):
        kw = Keyword.objects.create(name="django")
        item = _make_item(title="Django Tutorial", body="body")
        flag = Flag.objects.create(keyword=kw, content_item=item, score=100)
        r = self.client.patch(f"/flags/{flag.id}/", {"status": "irrelevant"}, content_type="application/json")
        self.assertEqual(r.status_code, 200)
        self.assertIsNotNone(r.json()["suppressed_at_content_version"])

    def test_trigger_scan(self):
        Keyword.objects.create(name="django")
        r = self.client.post("/scan/", {"source": "mock"}, content_type="application/json")
        self.assertEqual(r.status_code, 200)
        self.assertGreater(r.json()["flags_created"], 0)

class TestScoringIntegration(TestCase):
    """Verify scores are stored correctly on flags after a real scan."""

    def test_exact_title_match_stores_score_100(self):
        Keyword.objects.create(name="django")
        ScanService(source="mock").run()
        flag = Flag.objects.filter(
            keyword__name="django",
            content_item__title="Learn Django Fast"
        ).first()
        self.assertIsNotNone(flag)
        self.assertEqual(flag.score, 100)

    def test_body_only_match_stores_score_40(self):
        Keyword.objects.create(name="python")
        ScanService(source="mock").run()
        # "Learn Django Fast" body contains "python" but title does not
        flag = Flag.objects.filter(
            keyword__name="python",
            content_item__title="Learn Django Fast"
        ).first()
        self.assertIsNotNone(flag)
        self.assertEqual(flag.score, 40)

    def test_scan_summary_counts_are_accurate(self):
        Keyword.objects.create(name="django")
        result = ScanService(source="mock").run()
        self.assertEqual(result["content_items_processed"], 6)
        self.assertEqual(result["keywords_active"], 1)
        self.assertEqual(result["flags_skipped_suppressed"], 0)
        self.assertEqual(result["flags_updated"], 0)