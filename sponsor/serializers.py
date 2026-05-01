from rest_framework import serializers
from .models import Sponsor
import base64
import imghdr
import uuid
from django.core.files.base import ContentFile


class SponsorDetailSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    social = serializers.SerializerMethodField()

    class Meta:
        model = Sponsor
        fields = ['name', 'logo', 'url', 'social']

    def get_logo(self, obj):
        request = self.context.get('request')  # Only works in serializers with context
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        return None

    def get_social(self, obj):
        social = {
            "twitter": obj.twitter,
            "linkedin": obj.linkedin,
            "instagram": obj.instagram,
            "facebook": obj.facebook,
        }
        return {key: value for key, value in social.items() if value}

    # def get_logo(self, obj):
    #     if obj.logo:
    #         try:
    #             with obj.logo.open('rb') as image_file:
    #                 encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    #                 file_type = obj.logo.name.split('.')[-1]
    #                 return f"data:image/{file_type};base64,{encoded_string}"
    #         except Exception as e:
    #             return None
    #     return None
