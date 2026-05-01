from rest_framework import serializers

from .models import (
    CompanyOperationChoices,
    EventRegistration,
    Inquiry,
    JobLevelChoices,
    Panel,
    RegistrationTypeChoices,
    Ticket,
)

VALID_PRODUCT_IDS = {
    "online-casino",
    "sportsbook",
    "hybrid",
    "esports-betting",
    "fantasy-sports",
    "poker",
    "bingo",
    "ilottery",
    "sweepstake-casino",
    "social-casino",
    "landbased-casino",
    "retail-betting-shop",
}

VALID_INTEREST_IDS = {"exhibiting", "sponsoring", "attending"}


class EventRegistrationSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')
    company = serializers.CharField(source='company_name')
    email = serializers.EmailField(source='work_email')
    phone = serializers.CharField(source='phone_number')
    nationality = serializers.CharField()
    weburl = serializers.URLField(source='website_url', required=False, allow_null=True, allow_blank=True)
    jobTitle = serializers.CharField(source='job_title')
    jobLevel = serializers.ChoiceField(source='job_level', choices=JobLevelChoices.choices)
    companyOperation = serializers.ChoiceField(source='company_operation', choices=CompanyOperationChoices.choices)
    type = serializers.ChoiceField(source='form_type', choices=RegistrationTypeChoices.choices, required=False)
    brands = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    products = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    interests = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)

    class Meta:
        model = EventRegistration
        fields = [
            'type',
            'firstName',
            'lastName',
            'email',
            'phone',
            'nationality',
            'company',
            'weburl',
            'jobTitle',
            'jobLevel',
            'companyOperation',
            'brands',
            'products',
            'interests',
        ]

    def validate(self, attrs):
        form_type = attrs.get('form_type')
        has_products = bool(attrs.get('products'))
        has_interests = bool(attrs.get('interests'))
        phone = attrs.get('phone_number', '')
        products = attrs.get('products', [])
        interests = attrs.get('interests', [])

        if phone and (not phone.startswith('+') or not phone[1:].isdigit()):
            raise serializers.ValidationError({'phone': 'Phone number must be in international format, e.g. +254712345678.'})

        invalid_products = sorted(set(products) - VALID_PRODUCT_IDS)
        if invalid_products:
            raise serializers.ValidationError({'products': f'Invalid product IDs: {invalid_products}'})

        invalid_interests = sorted(set(interests) - VALID_INTEREST_IDS)
        if invalid_interests:
            raise serializers.ValidationError({'interests': f'Invalid interest IDs: {invalid_interests}'})

        if not form_type:
            form_type = RegistrationTypeChoices.OPERATOR if has_products else RegistrationTypeChoices.INTEREST
            attrs['form_type'] = form_type

        if form_type == RegistrationTypeChoices.OPERATOR:
            if not attrs.get('website_url'):
                raise serializers.ValidationError({'weburl': 'This field is required for operator registrations.'})
            if not attrs.get('brands'):
                raise serializers.ValidationError({'brands': 'At least one brand is required for operator registrations.'})
            if not has_products:
                raise serializers.ValidationError({'products': 'At least one product is required for operator registrations.'})
            if has_interests:
                raise serializers.ValidationError({'interests': 'This field is not allowed for operator registrations.'})

        if form_type == RegistrationTypeChoices.INTEREST:
            if attrs.get('website_url'):
                raise serializers.ValidationError({'weburl': 'This field is not allowed for interest registrations.'})
            if attrs.get('brands'):
                raise serializers.ValidationError({'brands': 'This field is not allowed for interest registrations.'})
            if has_products:
                raise serializers.ValidationError({'products': 'This field is not allowed for interest registrations.'})
            if not has_interests:
                raise serializers.ValidationError({'interests': 'At least one interest is required for interest registrations.'})

        return attrs

    def create(self, validated_data):
        brands_list = validated_data.pop('brands', [])
        products_list = validated_data.pop('products', [])
        interests_list = validated_data.pop('interests', [])
        validated_data['brands'] = ", ".join(brands_list)
        validated_data['products'] = ", ".join(products_list)
        validated_data['interests'] = ", ".join(interests_list)
        return EventRegistration.objects.create(**validated_data)


class InquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inquiry
        fields = ['name', 'email', 'topic', 'message']


class PanelSpeakerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    role = serializers.CharField(allow_null=True)
    company = serializers.CharField(allow_null=True)
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class PanelSerializer(serializers.ModelSerializer):
    panelName = serializers.CharField(source="name")
    time = serializers.DateTimeField(source="start_time")
    moderator = serializers.SerializerMethodField()
    speakers = serializers.SerializerMethodField()

    class Meta:
        model = Panel
        fields = ["id", "panelName", "description", "time", "location", "moderator", "speakers"]

    def get_moderator(self, obj):
        return PanelSpeakerSerializer(obj.moderator, context=self.context).data

    def get_speakers(self, obj):
        return PanelSpeakerSerializer(obj.speakers.all(), many=True, context=self.context).data


class TicketSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="stripe_price_id")
    doorPrice = serializers.DecimalField(source="door_price", max_digits=10, decimal_places=2, allow_null=True)
    isPopular = serializers.BooleanField(source="is_popular")
    priceIncreaseDate = serializers.DateTimeField(source="price_increase_date", allow_null=True)
    features = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            "id",
            "label",
            "price",
            "doorPrice",
            "isPopular",
            "description",
            "features",
            "priceIncreaseDate",
        ]

    def get_features(self, obj):
        return obj.get_features_list()
