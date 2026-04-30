from rest_framework import serializers
from .models import Speaker, BecomeASpeaker
import base64


class SocialLinksSerializer(serializers.Serializer):
    """
    A nested serializer for social links, only including non-null values.
    """
    twitter = serializers.URLField(required=False, allow_null=True)
    linkedin = serializers.URLField(required=False, allow_null=True)
    instagram = serializers.URLField(required=False, allow_null=True)
    website = serializers.URLField(required=False, allow_null=True)

    def to_representation(self, instance):
        # Only include fields that have a non-null value
        ret = super().to_representation(instance)
        return {key: value for key, value in ret.items() if value is not None and value != ''}


class SpeakerSerializer(serializers.ModelSerializer):
    """
    Serializer for the Speaker model, transforming its data into the desired API format.
    """
    # Use a SerializerMethodField to create the 'image' field with the full URL
    image = serializers.SerializerMethodField()

    # Use a SerializerMethodField to create the nested 'social' object
    social = SocialLinksSerializer(source='*', read_only=True)  # Use source='*' to pass the whole instance

    # Use a SerializerMethodField to convert the comma-separated events to a list
    events = serializers.SerializerMethodField()

    class Meta:
        model = Speaker
        fields = [
            'name',
            'company',
            'bio',
            'role',
            'image',
            'social',
            'events',
            'is_featured',
        ]

    def get_image(self, obj):
        request = self.context.get('request')  # Only works in serializers with context
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    # def get_image(self, obj):
    #     if obj.image:
    #         try:
    #             with obj.image.open('rb') as image_file:
    #                 encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    #                 file_type = obj.image.name.split('.')[-1]
    #                 return f"data:image/{file_type};base64,{encoded_string}"
    #         except Exception as e:
    #             return None
    #     return None

    def get_events(self, obj):
        # Use the get_event_list method from your Speaker model
        return obj.get_event_list()


class BecomeASpeakerSerializer(serializers.ModelSerializer):
    """
    Serializer for BecomeASpeaker model submissions.
    Accepts camelCase keys and maps to model fields.
    """
    
    class Meta:
        model = BecomeASpeaker
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'linkedin_profile',
            'job_title',
            'company_name',
            'website_url',
            'company_type',
            'type_of_participation',
            'talk_title',
            'topic_description',
            'supporting_files',
        ]
    
    def to_internal_value(self, data):
        # Map camelCase to snake_case for API compatibility
        camel_to_snake = {
            'firstName': 'first_name',
            'lastName': 'last_name',
            'phoneNumber': 'phone_number',
            'linkedinProfile': 'linkedin_profile',
            'jobTitle': 'job_title',
            'companyName': 'company_name',
            'websiteUrl': 'website_url',
            'companyType': 'company_type',
            'typeOfParticipation': 'type_of_participation',
            'talkTitle': 'talk_title',
            'topicDescription': 'topic_description',
            'supportingFiles': 'supporting_files',
        }
        
        # Convert camelCase keys to snake_case
        converted_data = {}
        for key, value in data.items():
            snake_key = camel_to_snake.get(key, key)
            converted_data[snake_key] = value
        
        return super().to_internal_value(converted_data)