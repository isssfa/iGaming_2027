from django.db import models
from django.contrib.auth.models import User
import os
import time
from django.utils.text import slugify


def sponsorship_icon_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    timestamp = int(time.time())
    sponsor_slug = slugify(instance.title)
    filename = f"{sponsor_slug}_{timestamp}.{ext}"
    return os.path.join('sponsorship', filename)


class Sponsorship(models.Model):
    """
    Represents a sponsorship package for the iGaming AFRIKA Summit 2026.
    """
    # Core Sponsorship Details
    title = models.CharField(blank=True, null=True, max_length=255, help_text="Title of the sponsorship package (e.g., 'Headline Sponsor')")
    price = models.CharField(max_length=50, help_text="Price of the sponsorship package (e.g., '$55,000')")
    status = models.CharField(
        max_length=50,
        choices=[
            ('AVAILABLE', 'Available'),
            ('SOLD', 'Sold'),
            ('ON HOLD', 'On Hold'),
            ('PENDING', 'Pending')
        ],
        default='AVAILABLE',
        help_text="Current availability status of the sponsorship package"
    )
    icon = models.CharField(blank=True, null=True, max_length=50, help_text="Emoji or shortcode for an icon (e.g., '🎤')")
    iconBg = models.CharField(max_length=50, blank=True, null=True, help_text="Background color class for the icon (e.g., 'bg-green-400')")
    description = models.TextField(blank=True, null=True, help_text="General description or special notes (e.g., '*bespoke package pricing available on request*')")

    # Benefits Sections (using TextField for flexibility, allowing markdown/bullet points)
    benefits = models.TextField(blank=True, help_text="Comma-separated or newline-separated list of general benefits")
    platinum_benefits = models.TextField(blank=True, help_text="Comma-separated or newline-separated list of Platinum benefits")
    diamond_benefits = models.TextField(blank=True, null=True, help_text="Comma-separated or newline-separated list of Diamond benefits")
    gold_benefits = models.TextField(blank=True, help_text="Comma-separated or newline-separated list of Gold benefits")
    silver_benefits = models.TextField(blank=True, help_text="Comma-separated or newline-separated list of Silver benefits")
    bronze_benefits = models.TextField(blank=True, help_text="Comma-separated or newline-separated list of Bronze benefits")

    notes = models.TextField(blank=True, help_text="Additional notes or responsibilities (e.g., '*Venue branding is the responsibility of the sponsor*')")

    tickets = models.TextField(blank=True, help_text="Details about included tickets (e.g., '40 Premium Passes...')")

    icon_image = models.ImageField(upload_to=sponsorship_icon_upload_path, blank=True, null=True)

    total_avalibility = models.IntegerField(default=0, help_text="Total number of sponsorship packages available.")

    total_sold = models.IntegerField(default=0, help_text="Total number of sponsorship packages sold.")

    # Automatic Tracking Fields
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time when the sponsorship record was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time when the sponsorship record was last updated.")
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='added_sponsorships',
        help_text="The user who added this sponsorship record (auto-filled)."
    )

    class Meta:
        verbose_name = "Sponsorship Package"
        verbose_name_plural = "Sponsorship Packages"
        ordering = ['price']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)