from rest_framework import serializers
from .models import Nomination


class NominationSerializer(serializers.ModelSerializer):
    """
    Serializer for Nomination model submissions.
    Accepts camelCase keys and maps to model fields.
    """

    # Ensure award_category is treated as a list of strings
    award_category = serializers.ListField(
        child=serializers.CharField(),
        allow_null=True,
        required=False
    )

    class Meta:
        model = Nomination
        fields = [
            'full_name',
            'email',
            'phone_number',
            'linkedin_url',
            'company',
            'role',
            'nominated_company',
            'award_category',
            'background_information',
            'specific_instance_project',
            'impact_on_industry',
        ]
    
    def to_internal_value(self, data):
        """
        Map various frontend key styles (camelCase, other custom names)
        to the actual model field names.
        """
        camel_to_snake = {
            # Basic identity fields
            'fullName': 'full_name',

            # Phone / LinkedIn
            'phoneNumber': 'phone_number',
            'phone': 'phone_number',
            'linkedinUrl': 'linkedin_url',
            'linkedin': 'linkedin_url',

            # Company fields
            'companyName': 'company',
            'nominatedCompany': 'nominated_company',

            # Award categories (list)
            'awardCategory': 'award_category',

            # Question mappings from current payload
            # reasonForNomination -> background_information (Q1)
            'reasonForNomination': 'background_information',
            # specialContribution -> specific_instance_project (Q2)
            'specialContribution': 'specific_instance_project',
            # impactOfNominee -> impact_on_industry (Q3)
            'impactOfNominee': 'impact_on_industry',

            # Old camelCase names (if still used anywhere)
            'backgroundInformation': 'background_information',
            'specificInstanceProject': 'specific_instance_project',
            'impactOnIndustry': 'impact_on_industry',
        }

        # Convert incoming keys to the expected field names
        converted_data = {}
        for key, value in data.items():
            snake_key = camel_to_snake.get(key, key)
            converted_data[snake_key] = value

        return super().to_internal_value(converted_data)
        
        