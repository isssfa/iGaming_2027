from django.db import models
from django.contrib.auth.models import User



class EventRegistration(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="registrations")
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    work_email = models.EmailField(null=True, blank=True)
    interests = models.TextField(help_text="Comma-separated list of interests", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.company_name}"


class Inquiry(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    topic = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"Inquiry from {self.name} - {self.topic}"


