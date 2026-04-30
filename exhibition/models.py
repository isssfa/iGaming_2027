from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import os
import time
from django.utils.text import slugify

User = get_user_model()

class ExhibitionTier(models.Model):
    """
    Represents the different tiers of exhibition packages (e.g., Platinum, Gold).
    """
    name = models.CharField(max_length=50, unique=True, help_text="Name of the exhibition tier (e.g., 'Platinum', 'Gold')")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='added_tiers',
        verbose_name=_("Added by"),
        help_text=_("The user who created this tier.")
    )

    class Meta:
        verbose_name = _("Exhibition Tier")
        verbose_name_plural = _("Exhibition Tiers")
        ordering = ['name']

    def __str__(self):
        return self.name

class ExhibitionOption(models.Model):
    """
    Represents a specific exhibition option within a tier (e.g., Space Only, Shell Scheme).
    """
    tier = models.ForeignKey(ExhibitionTier, on_delete=models.CASCADE, related_name='options', help_text="The tier this option belongs to.")
    type = models.CharField(max_length=100, help_text="Type of stand (e.g., 'Space Only Scheme', 'Shell Scheme')")
    stand_size = models.CharField(max_length=50, help_text="Size of the stand (e.g., '6x5', '4 X 4')")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price of the exhibition option.")
    description = models.TextField(help_text="Detailed description of the exhibition option.")

    # Benefits (using TextField for flexibility, consider a separate model if individual benefits need more fields)
    stand_benefits = models.TextField(blank=True, null=True, help_text="Comma-separated or newline-separated list of benefits related to the stand.")
    exhibitor_benefits = models.TextField(blank=True, null=True, help_text="Comma-separated or newline-separated list of general exhibitor benefits.")
    sponsorship_status = models.TextField(blank=True, null=True, help_text="Comma-separated or newline-separated list of sponsorship status details.")
    notes = models.TextField(blank=True, null=True, help_text="Comma-separated or newline-separated list of additional notes for this option.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='added_exhibition_options',
        verbose_name=_("Added by"),
        help_text=_("The user who created this exhibition option.")
    )

    class Meta:
        verbose_name = _("Exhibition Option")
        verbose_name_plural = _("Exhibition Options")
        unique_together = ('tier', 'type', 'stand_size') # Ensures unique options within a tier

    def __str__(self):
        return f"{self.tier.name} - {self.type} ({self.stand_size})"


def exhibition_image_upload_path(instance, filename):
    """
    Generates a unique path for exhibition images based on tier, type, and timestamp.
    Example: 'exhibition_images/platinum_shell-scheme_1678886400.jpg'
    """
    ext = filename.split('.')[-1]
    timestamp = int(time.time())
    file_name = slugify(filename.split('.')[:-1])

    # Access the related ExhibitionOption instance
    option = instance.option

    # Get tier name and type from the associated option
    tier_name = slugify(option.tier.name) if option.tier else 'unknown_tier'
    option_type = slugify(option.type) if option.type else 'unknown_type'

    # Construct the new filename
    new_filename = f"{tier_name}_{option_type}_{file_name}_{timestamp}.{ext}"

    # Return the full path
    return os.path.join('exhibition_images', new_filename)


class ExhibitionImage(models.Model):
    """
    Represents an image associated with an exhibition option, stored as Base64.
    """
    option = models.ForeignKey(ExhibitionOption, on_delete=models.CASCADE, related_name='images', help_text="The exhibition option this image belongs to.")
    # Storing Base64 string directly. Consider a separate file storage solution for production.
    image = models.ImageField(upload_to=exhibition_image_upload_path, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='added_exhibition_images',
        verbose_name=_("Added by"),
        help_text=_("The user who added this image.")
    )

    class Meta:
        verbose_name = _("Exhibition Image")
        verbose_name_plural = _("Exhibition Images")
        ordering = ['option']

    def __str__(self):
        return f"Image for {self.option}"