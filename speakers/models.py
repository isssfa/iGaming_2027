from django.db import models
from django.contrib.auth.models import User
import os
import time
from django.utils.text import slugify


def speaker_image_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    timestamp = int(time.time())
    sponsor_slug = slugify(instance.name)
    filename = f"{sponsor_slug}_{timestamp}.{ext}"
    return os.path.join('speakers', filename)


class Speaker(models.Model):
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, blank=True, null=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to=speaker_image_upload_path, null=True, blank=True)

    # Social Links
    twitter = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    # Comma-separated events field
    events = models.TextField(
        help_text="Comma-separated list of events",
        null=True,
        blank=True
    )

    is_featured = models.BooleanField(default=False)

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='speakers_added'
    )

    def __str__(self):
        return self.name

    def get_event_list(self):
        """Returns the events as a list"""
        return [event.strip() for event in self.events.split(",")] if self.events else []


def speaker_supporting_file_upload_path(instance, filename):
    """Generate upload path for speaker supporting files"""
    ext = filename.split('.')[-1]
    timestamp = int(time.time())
    return os.path.join('speakers', 'supporting_files', f"{timestamp}_{filename}")


class BecomeASpeaker(models.Model):
    """Model for 'Become a Speaker' submissions"""
    
    COMPANY_TYPE_CHOICES = [
        ('Affiliate', 'Affiliate'),
        ('Agency', 'Agency'),
        ('Broker', 'Broker'),
        ('Game Provider', 'Game Provider'),
        ('Investor', 'Investor'),
        ('Legal', 'Legal'),
        ('Media', 'Media'),
        ('non-gaming Supplier', 'non-gaming Supplier'),
        ('Operator', 'Operator'),
        ('Other', 'Other'),
        ('Regulator', 'Regulator'),
        ('Start-up', 'Start-up'),
        ('Supplier', 'Supplier'),
        ('Financial Institution', 'Financial Institution'),
        ('Payments', 'Payments'),
        ('Nonprofit', 'Nonprofit'),
    ]
    
    PARTICIPATION_TYPE_CHOICES = [
        ('Conference Speaker', 'Conference Speaker'),
        ('Podcast Participation', 'Podcast Participation'),
        ('All of them', 'All of them'),
    ]
    
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    linkedin_profile = models.URLField(blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)
    company_type = models.CharField(
        max_length=50,
        choices=COMPANY_TYPE_CHOICES,
        blank=True,
        null=True
    )
    type_of_participation = models.CharField(
        max_length=50,
        choices=PARTICIPATION_TYPE_CHOICES,
        blank=True,
        null=True
    )
    talk_title = models.CharField(max_length=255, blank=True, null=True)
    topic_description = models.TextField(blank=True, null=True)
    supporting_files = models.FileField(
        upload_to=speaker_supporting_file_upload_path,
        blank=True,
        null=True
    )
    email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"