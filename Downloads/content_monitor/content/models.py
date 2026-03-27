from django.db import models


class ContentItem(models.Model):
    title = models.CharField(max_length=500)
    source = models.CharField(max_length=100)
    body = models.TextField()
    last_updated = models.DateTimeField()
    external_id = models.CharField(max_length=512, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.source}] {self.title}"

    class Meta:
        ordering = ['-last_updated']