import uuid

from django.contrib.auth.models import User
from django.db import models


class Category(models.Model):
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    priority = models.PositiveIntegerField(default=0, help_text="Lower values appear first.")
    added_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='awards_categories',
    )

    class Meta:
        ordering = ['priority', 'title']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.title


class Nominee(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='nominees')
    nominee = models.CharField(max_length=255)
    added_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='awards_nominees',
    )

    class Meta:
        ordering = ['category__priority', 'nominee']
        unique_together = ('category', 'nominee')

    def __str__(self):
        return f"{self.nominee} ({self.category.title})"


class Vote(models.Model):
    voter_name = models.CharField(max_length=255)
    voter_email = models.EmailField(db_index=True)
    company = models.CharField(max_length=255, blank=True, default='')
    position = models.CharField(max_length=255, blank=True, default='')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='votes')
    nominee = models.ForeignKey(Nominee, on_delete=models.CASCADE, related_name='votes')
    batch_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    confirmation_token = models.CharField(max_length=64, db_index=True)
    email_sent = models.BooleanField(default=False)
    is_confirmed = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['voter_email', 'is_confirmed']),
            models.Index(fields=['confirmation_token', 'voter_email']),
        ]
        unique_together = ('voter_email', 'category', 'is_confirmed')

    def __str__(self):
        return f"{self.voter_email} -> {self.nominee.nominee} [{self.category.title}]"

