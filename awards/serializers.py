from rest_framework import serializers

from .models import Category, Nominee


class NomineeSerializer(serializers.ModelSerializer):
    nominee_id = serializers.IntegerField(source='id')

    class Meta:
        model = Nominee
        fields = ['nominee_id', 'nominee']


class CategoryWithNomineesSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(source='id')
    category_title = serializers.CharField(source='title')
    nominees = NomineeSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['category_id', 'category_title', 'description', 'priority', 'nominees']


class VoteItemSerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    category_title = serializers.CharField(required=False, allow_blank=True)
    nominee_id = serializers.IntegerField()
    nominee = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        category_id = attrs['category_id']
        nominee_id = attrs['nominee_id']

        try:
            nominee_obj = Nominee.objects.select_related('category').get(
                id=nominee_id,
                category_id=category_id,
            )
        except Nominee.DoesNotExist:
            raise serializers.ValidationError(
                "Nominee does not exist for the selected category."
            )

        attrs['category_obj'] = nominee_obj.category
        attrs['nominee_obj'] = nominee_obj
        return attrs


class VoteSubmissionSerializer(serializers.Serializer):
    voter_name = serializers.CharField(max_length=255)
    voter_email = serializers.EmailField()
    company = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    position = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    votes = VoteItemSerializer(many=True, allow_empty=False)

    def to_internal_value(self, data):
        camel_to_snake = {
            'companyName': 'company',
            'voterName': 'voter_name',
            'voterEmail': 'voter_email',
        }
        if isinstance(data, dict):
            converted = {}
            for key, value in data.items():
                converted[camel_to_snake.get(key, key)] = value
            data = converted
        return super().to_internal_value(data)

    def validate(self, attrs):
        votes = attrs.get("votes") or []
        category_ids = [v["category_obj"].id for v in votes]
        if len(category_ids) != len(set(category_ids)):
            raise serializers.ValidationError(
                {
                    "votes": "Each category may only appear once in your submission. "
                    "Remove duplicate categories and try again."
                }
            )
        return attrs

