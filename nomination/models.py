from django.db import models
from django.contrib.auth.models import User


class Nomination(models.Model):
    """
    Model for award nominations.
    Captures information about the nominator and the nominated company.
    """
    full_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    linkedin_url = models.URLField(null=True, blank=True)
    company = models.CharField(max_length=255, null=True, blank=True)
    role = models.CharField(max_length=255, null=True, blank=True)
    nominated_company = models.CharField(max_length=255, null=True, blank=True)
    # Store list of award categories as JSON (list of strings)
    award_category = models.JSONField(null=True, blank=True, default=list)
    
    # Questions
    background_information = models.TextField(null=True, blank=True)  # Question 1
    specific_instance_project = models.TextField(null=True, blank=True)  # Question 2
    impact_on_industry = models.TextField(null=True, blank=True)  # Question 3
    
    # Status and audit fields
    email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.nominated_company} ({self.award_category})"


