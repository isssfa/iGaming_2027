from rest_framework import serializers
from .models import EventRegistration, Inquiry
import base64
import imghdr
import uuid
from django.core.files.base import ContentFile

class EventRegistrationSerializer(serializers.ModelSerializer):
    # Accept camelCase keys and map to model
    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')
    company = serializers.CharField(source='company_name')
    email = serializers.EmailField(source='work_email')
    phone = serializers.CharField(source='phone_number')
    interests = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = EventRegistration
        fields = ['firstName', 'lastName', 'company', 'phone', 'email', 'interests']

    def create(self, validated_data):
        interests_list = validated_data.pop('interests', [])
        validated_data['interests'] = ", ".join(interests_list)
        return EventRegistration.objects.create(**validated_data)


class InquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inquiry
        fields = ['name', 'email', 'topic', 'message']
