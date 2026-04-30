from django import forms
from django.core.exceptions import ValidationError
from .models import Sponsor


class SponsorAdminForm(forms.ModelForm):
    """Custom form for Sponsor admin with validation for sponsorship package availability."""
    
    class Meta:
        model = Sponsor
        fields = '__all__'
    
    def clean_sponsorship_package(self):
        """
        Validate that sponsorship packages are not full before allowing attachment.
        """
        selected_packages = self.cleaned_data.get('sponsorship_package', [])
        
        # If this is an update, get the currently attached packages
        if self.instance and self.instance.pk:
            current_packages = set(self.instance.sponsorship_package.all())
        else:
            current_packages = set()
        
        # Get newly added packages (packages that will be added)
        new_packages = set(selected_packages) - current_packages
        
        # Check each newly added package for availability
        errors = []
        for package in new_packages:
            # Check if package is already full or would exceed availability
            if package.total_sold >= package.total_avalibility:
                errors.append(
                    ValidationError(
                        f"'{package.title}' is already full. "
                        f"Availability: {package.total_avalibility}, "
                        f"Already sold: {package.total_sold}. "
                        f"Cannot attach additional sponsors.",
                        code='package_full'
                    )
                )
            # Check if adding this sponsor would exceed availability
            elif package.total_sold + 1 > package.total_avalibility:
                errors.append(
                    ValidationError(
                        f"Cannot attach sponsor to '{package.title}'. "
                        f"Adding this sponsor would exceed availability. "
                        f"Current: {package.total_sold}/{package.total_avalibility}",
                        code='exceeds_availability'
                    )
                )
        
        # If there are errors, raise them
        if errors:
            raise ValidationError(errors)
        
        return selected_packages

