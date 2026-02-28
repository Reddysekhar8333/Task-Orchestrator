import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Task(models.Model):
    TASK_TYPES = [
        ('DATA_PROCESSING', 'Data Processing'),
        ('FILE_CONVERSION', 'File Conversion'),
        ('IMAGE_PROCESSING', 'Image Processing'),
        ('REPORT_GENERATION', 'Report Generation'),
        ('EMAIL_NOTIFICATION', 'Email Notification'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Critical'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks')

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    task_type = models.CharField(max_length=50, choices=TASK_TYPES, default='DATA_PROCESSING')
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict, blank=True)
    input_file = models.FileField(upload_to='task_inputs/', null=True, blank=True)
    output_file = models.FileField(upload_to='task_outputs/', null=True, blank=True)

    progress = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)

    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['task_type', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user', 'status', 'created_at']),
            models.Index(fields=['priority', 'status', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.status}"

    def save(self, *args, **kwargs):
        if self.status == 'PROCESSING' and not self.started_at:
            self.started_at = timezone.now()
        elif self.status == 'COMPLETED' and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def processing_time(self):
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None