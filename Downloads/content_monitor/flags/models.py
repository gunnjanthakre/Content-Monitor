from django.db import models


class Flag(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RELEVANT = 'relevant', 'Relevant'
        IRRELEVANT = 'irrelevant', 'Irrelevant'

    keyword = models.ForeignKey(
        'keywords.Keyword',
        on_delete=models.CASCADE,
        related_name='flags',
    )
    content_item = models.ForeignKey(
        'content.ContentItem',
        on_delete=models.CASCADE,
        related_name='flags',
    )
    score = models.IntegerField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    suppressed_at_content_version = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_irrelevant(self, content_last_updated):
        self.status = self.Status.IRRELEVANT
        self.suppressed_at_content_version = content_last_updated
        self.save(update_fields=['status', 'suppressed_at_content_version', 'updated_at'])

    def is_suppressed_for(self, content_last_updated) -> bool:
        if self.status != self.Status.IRRELEVANT:
            return False
        return self.suppressed_at_content_version == content_last_updated

    def __str__(self):
        return f"Flag({self.keyword} / {self.content_item_id} / {self.status})"

    class Meta:
        unique_together = [('keyword', 'content_item')]
        ordering = ['-score', '-created_at']