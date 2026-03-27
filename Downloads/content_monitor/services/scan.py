from content.models import ContentItem
from flags.models import Flag
from keywords.models import Keyword
from services.matching import compute_score
from services.sources import fetch_mock


class ScanService:
    def __init__(self, source: str = "mock"):
        self.source = source

    def run(self) -> dict:
        raw_records = self._fetch_records()
        content_items = self._upsert_content_items(raw_records)
        keywords = list(Keyword.objects.all())
        if not keywords:
            return {
                "source": self.source,
                "content_items_processed": len(content_items),
                "keywords_active": 0,
                "flags_created": 0,
                "flags_updated": 0,
                "flags_skipped_suppressed": 0,
                }

        created = updated = skipped = 0

        for item in content_items:
            for keyword in keywords:
                score = compute_score(keyword.name, item.title, item.body)
                if score == 0:
                    continue
                result = self._upsert_flag(keyword, item, score)
                if result == "created":
                    created += 1
                elif result == "updated":
                    updated += 1
                else:
                    skipped += 1

        return {
            "source": self.source,
            "content_items_processed": len(content_items),
            "keywords_active": len(keywords),
            "flags_created": created,
            "flags_updated": updated,
            "flags_skipped_suppressed": skipped,
        }

    def _fetch_records(self) -> list[dict]:
        if self.source == "mock":
            return fetch_mock()
        raise ValueError(f"Unknown source: {self.source!r}")

    def _upsert_content_items(self, records: list[dict]) -> list[ContentItem]:
        items = []
        for rec in records:
            obj, created = ContentItem.objects.get_or_create(
                external_id=rec["external_id"],
                defaults={
                    "title": rec["title"],
                    "body": rec["body"],
                    "source": rec["source"],
                    "last_updated": rec["last_updated"],
                },
            )
            if not created and obj.last_updated != rec["last_updated"]:
                obj.title = rec["title"]
                obj.body = rec["body"]
                obj.last_updated = rec["last_updated"]
                obj.save(update_fields=["title", "body", "last_updated"])
            items.append(obj)
        return items

    def _upsert_flag(self, keyword: Keyword, item: ContentItem, score: int) -> str:
        try:
            flag = Flag.objects.get(keyword=keyword, content_item=item)
        except Flag.DoesNotExist:
            Flag.objects.create(
                keyword=keyword,
                content_item=item,
                score=score,
                status=Flag.Status.PENDING,
            )
            return "created"

        if flag.is_suppressed_for(item.last_updated):
            return "skipped"

        needs_save = False

        if flag.status == Flag.Status.IRRELEVANT:
            flag.status = Flag.Status.PENDING
            flag.suppressed_at_content_version = None
            needs_save = True

        if flag.score != score:
            flag.score = score
            needs_save = True

        if needs_save:
            flag.save(update_fields=["status", "score", "suppressed_at_content_version", "updated_at"])
            return "updated"

        return "skipped"