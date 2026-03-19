from django.db import models


class HealthTip(models.Model):
    """Health tips shown on the dashboard."""

    title = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    source = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dashboard_healthtip'
        verbose_name = 'Health Tip'
        verbose_name_plural = 'Health Tips'
        ordering = ['-created_at']

    def __str__(self):
        title = self.title.strip() if self.title else ''
        return title or f"Health Tip {self.id}"

    