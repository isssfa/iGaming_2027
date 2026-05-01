from django.db import models
from django.contrib.auth.models import User


class JobLevelChoices(models.TextChoices):
    ENTRY_LEVEL = "Entry Level", "Entry Level"
    ASSOCIATE = "Associate", "Associate"
    MID_SENIOR = "Mid-Senior Level", "Mid-Senior Level"
    DIRECTOR = "Director", "Director"
    EXECUTIVE = "Executive", "Executive"
    C_SUITE = "C-Suite", "C-Suite"
    OWNER_PARTNER = "Owner/Partner", "Owner/Partner"
    INTERN = "Intern", "Intern"
    OTHER = "Other", "Other"


class CompanyOperationChoices(models.TextChoices):
    OPERATOR = "Operator", "Operator"
    AFFILIATE = "Affiliate", "Affiliate"
    INVESTOR = "Investor", "Investor"
    MEDIA = "Media", "Media"
    REGULATOR = "Regulator", "Regulator"
    NON_PROFIT = "Non-profit", "Non-profit"
    SPORTS_ORG = "Sports Organisation", "Sports Organisation"
    SUPPLIER = "Supplier/Service Provider", "Supplier/Service Provider"


class RegistrationTypeChoices(models.TextChoices):
    OPERATOR = "operator", "Operator"
    INTEREST = "interest", "Interest"


class EventRegistration(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="registrations")
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    work_email = models.EmailField(null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True)
    website_url = models.URLField(null=True, blank=True)
    job_title = models.CharField(max_length=255, null=True, blank=True)
    job_level = models.CharField(max_length=40, choices=JobLevelChoices.choices, null=True, blank=True)
    company_operation = models.CharField(max_length=50, choices=CompanyOperationChoices.choices, null=True, blank=True)
    form_type = models.CharField(max_length=20, choices=RegistrationTypeChoices.choices, null=True, blank=True)
    brands = models.TextField(help_text="Comma-separated list of brands", null=True, blank=True)
    products = models.TextField(help_text="Comma-separated list of product IDs", null=True, blank=True)
    interests = models.TextField(help_text="Comma-separated list of interest IDs", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    email_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.company_name}"

    def get_brands_list(self):
        return [item.strip() for item in self.brands.split(",")] if self.brands else []

    def get_products_list(self):
        return [item.strip() for item in self.products.split(",")] if self.products else []

    def get_interests_list(self):
        return [item.strip() for item in self.interests.split(",")] if self.interests else []


class Inquiry(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    topic = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"Inquiry from {self.name} - {self.topic}"


class Panel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_time = models.DateTimeField()
    location = models.CharField(max_length=255)
    moderator = models.ForeignKey("speakers.Speaker", on_delete=models.PROTECT, related_name="moderated_panels")
    speakers = models.ManyToManyField("speakers.Speaker", related_name="panels", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_time", "name"]

    def __str__(self):
        return self.name


class Ticket(models.Model):
    stripe_price_id = models.CharField(max_length=255, unique=True)
    label = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    door_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_popular = models.BooleanField(default=False)
    description = models.CharField(max_length=255, blank=True, null=True)
    features = models.TextField(help_text="Newline-separated list of features", blank=True, null=True)
    price_increase_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["price", "label"]

    def __str__(self):
        return f"{self.label} ({self.stripe_price_id})"

    def get_features_list(self):
        if not self.features:
            return []
        return [item.strip() for item in self.features.splitlines() if item.strip()]


