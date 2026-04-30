import json
import os

from rest_framework import serializers

from .models import AffiliateApplication, AffiliateProofAttachment

ALLOWED_TRAFFIC_SOURCES = {
    'Web',
    'Facebook',
    'Telegram',
    'Whatsapp',
    'Twitter/X',
    'Offline',
    'Instagram',
    'Tiktok',
    'Youtube',
    'Linkedin',
    'Other',
}

# Sources that require a detail string (URL or handle) in traffic_source_details
SOURCES_REQUIRING_DETAIL = {
    'Web',
    'Facebook',
    'Telegram',
    'Whatsapp',
    'Twitter/X',
    'Instagram',
    'Tiktok',
    'Youtube',
    'Linkedin',
}

MAX_PROOF_BYTES = 2 * 1024 * 1024
ALLOWED_PROOF_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf'}
EXTRA_LABEL = 'Extra'


def _validate_proof_file_upload(value):
    if not value:
        return
    if getattr(value, 'size', None) == 0:
        return
    if value.size > MAX_PROOF_BYTES:
        raise serializers.ValidationError('File must be 2MB or smaller.')
    _, ext = os.path.splitext(value.name or '')
    ext = ext.lower()
    if ext not in ALLOWED_PROOF_EXTENSIONS:
        raise serializers.ValidationError(
            'Accepted formats: .jpg, .jpeg, .png, .pdf.',
        )


def _normalize_details(raw):
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return {str(k).strip(): (v if v is None else str(v).strip()) for k, v in raw.items()}
    raise serializers.ValidationError('Invalid traffic source details format.')


class AffiliateApplicationSerializer(serializers.ModelSerializer):
    """Multipart registration; per-source details + multiple proof rows."""

    firstName = serializers.CharField(source='first_name', max_length=120)
    lastName = serializers.CharField(source='last_name', max_length=120)
    phoneNumber = serializers.CharField(source='phone', max_length=40)
    isAffiliate = serializers.BooleanField(source='is_affiliate')
    trafficSources = serializers.CharField(source='traffic_sources')
    trafficSourceOtherLabel = serializers.CharField(
        source='traffic_source_other_label',
        required=False,
        allow_blank=True,
        default='',
        max_length=255,
    )
    trafficSourceDetails = serializers.JSONField(source='traffic_source_details')
    trafficRegions = serializers.CharField(source='traffic_regions')
    trafficVolume = serializers.CharField(source='traffic_volume', max_length=255)
    paymentPreferences = serializers.CharField(source='payment_preferences')
    paymentOtherDetail = serializers.CharField(
        source='payment_other_detail',
        required=False,
        allow_blank=True,
        default='',
        max_length=255,
    )
    proofUrlItems = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        default='[]',
    )
    additionalNotes = serializers.CharField(
        source='additional_notes',
        required=False,
        allow_blank=True,
        default='',
    )

    class Meta:
        model = AffiliateApplication
        fields = [
            'firstName',
            'lastName',
            'email',
            'phoneNumber',
            'isAffiliate',
            'trafficSources',
            'trafficSourceOtherLabel',
            'trafficSourceDetails',
            'trafficRegions',
            'trafficVolume',
            'paymentPreferences',
            'paymentOtherDetail',
            'proofUrlItems',
            'additionalNotes',
        ]

    def validate_trafficSources(self, value):
        parts = [p.strip() for p in (value or '').split(',') if p.strip()]
        if not parts:
            raise serializers.ValidationError('Select at least one traffic source.')
        unknown = [p for p in parts if p not in ALLOWED_TRAFFIC_SOURCES]
        if unknown:
            raise serializers.ValidationError(
                f'Invalid traffic source(s): {", ".join(unknown)}',
            )
        return ', '.join(parts)

    def validate_trafficSourceDetails(self, value):
        if isinstance(value, str):
            if not (value or '').strip():
                return {}
            try:
                value = json.loads(value)
            except json.JSONDecodeError as e:
                raise serializers.ValidationError(
                    'Invalid JSON for traffic source details.',
                ) from e
        return _normalize_details(value)

    def validate(self, attrs):
        request = self.context.get('request')
        selected = [p.strip() for p in attrs['traffic_sources'].split(',') if p.strip()]
        details = attrs.get('traffic_source_details') or {}
        other_label = (attrs.get('traffic_source_other_label') or '').strip()
        payment_prefs_raw = (attrs.get('payment_preferences') or '').strip()
        payment_other = (attrs.get('payment_other_detail') or '').strip()

        if 'Other' in selected:
            if not other_label:
                raise serializers.ValidationError(
                    {'trafficSourceOtherLabel': 'Describe your other traffic source.'},
                )
            attrs['traffic_source_other_label'] = other_label
        else:
            attrs['traffic_source_other_label'] = ''

        for src in SOURCES_REQUIRING_DETAIL:
            if src not in selected:
                continue
            val = (details.get(src) or '').strip()
            if not val:
                raise serializers.ValidationError(
                    {
                        'trafficSourceDetails': (
                            f'Provide URL or username/handle for {src}.'
                        ),
                    },
                )

        clean_details = {}
        for src in selected:
            if src == 'Offline':
                continue
            if src == 'Other':
                clean_details['Other'] = (details.get('Other') or '').strip()
            elif src in SOURCES_REQUIRING_DETAIL:
                clean_details[src] = (details.get(src) or '').strip()
        attrs['traffic_source_details'] = clean_details

        payment_parts = [p.strip() for p in payment_prefs_raw.split(',') if p.strip()]
        if not payment_parts:
            raise serializers.ValidationError(
                {'paymentPreferences': 'Select at least one payment preference.'},
            )
        normalized = []
        for p in payment_parts:
            if p in ('Revshare', 'revshare'):
                normalized.append('Revshare')
            elif p in ('CPA', 'cpa'):
                normalized.append('CPA')
            elif p in ('Hybrid', 'hybrid'):
                normalized.append('Hybrid')
            elif p in ('Cash payment', 'cash_payment'):
                normalized.append('Cash payment')
            elif p in ('Other', 'other'):
                normalized.append('Other')
            else:
                raise serializers.ValidationError(
                    {'paymentPreferences': f'Invalid payment option: {p}'},
                )
        # de-dupe preserve order
        seen = set()
        normalized_unique = []
        for p in normalized:
            if p in seen:
                continue
            seen.add(p)
            normalized_unique.append(p)
        attrs['payment_preferences'] = ', '.join(normalized_unique)

        if 'Other' in normalized_unique:
            if not payment_other:
                raise serializers.ValidationError(
                    {'paymentOtherDetail': 'Specify your preferred payment means.'},
                )
            attrs['payment_other_detail'] = payment_other
        else:
            attrs['payment_other_detail'] = ''

        proof_url_items = attrs.pop('proofUrlItems', None)
        if proof_url_items is None or proof_url_items == '':
            proof_url_items = self.initial_data.get('proofUrlItems', '[]')
        if isinstance(proof_url_items, str):
            try:
                proof_url_items = json.loads(proof_url_items or '[]')
            except json.JSONDecodeError as e:
                raise serializers.ValidationError(
                    {'proofUrlItems': 'Invalid JSON.'},
                ) from e

        if not isinstance(proof_url_items, list):
            raise serializers.ValidationError({'proofUrlItems': 'Expected a list.'})

        allowed_labels = set(selected) | {EXTRA_LABEL}
        normalized_urls = []
        for i, item in enumerate(proof_url_items):
            if not isinstance(item, dict):
                raise serializers.ValidationError({'proofUrlItems': f'Invalid item at index {i}.'})
            label = (item.get('label') or '').strip()
            url = (item.get('url') or '').strip()
            if not label:
                raise serializers.ValidationError(
                    {'proofUrlItems': f'Missing label for proof URL at index {i}.'},
                )
            if label not in allowed_labels:
                raise serializers.ValidationError(
                    {
                        'proofUrlItems': (
                            f'Label "{label}" must be one of your selected sources or Extra.'
                        ),
                    },
                )
            if not url:
                continue
            if not (url.startswith('http://') or url.startswith('https://')):
                raise serializers.ValidationError(
                    {'proofUrlItems': 'Each proof URL must start with http:// or https://.'},
                )
            normalized_urls.append({'label': label, 'url': url})

        files = []
        labels = []
        if request:
            files = request.FILES.getlist('proofFiles')
            raw_labels = request.data.get('proofFileLabels', '[]')
            try:
                labels = json.loads(raw_labels) if isinstance(raw_labels, str) else raw_labels
            except json.JSONDecodeError as e:
                raise serializers.ValidationError(
                    {'proofFiles': 'Invalid proofFileLabels JSON.'},
                ) from e
            if not isinstance(labels, list):
                raise serializers.ValidationError({'proofFiles': 'proofFileLabels must be a list.'})
            if len(files) != len(labels):
                raise serializers.ValidationError(
                    {'proofFiles': 'Each uploaded file must have a matching label in proofFileLabels.'},
                )
            for i, f in enumerate(files):
                _validate_proof_file_upload(f)
                lab = str(labels[i]).strip()
                if not lab:
                    raise serializers.ValidationError({'proofFiles': f'Missing label for file {i}.'})
                if lab not in allowed_labels:
                    raise serializers.ValidationError(
                        {'proofFiles': f'Invalid label "{lab}" for file {i}.'},
                    )

        if not normalized_urls and not files:
            raise serializers.ValidationError(
                'Provide at least one proof URL or upload at least one proof file.',
            )

        self._proof_url_rows = normalized_urls
        self._proof_file_pairs = list(zip(labels, files))
        return attrs

    def create(self, validated_data):
        validated_data.pop('proofUrlItems', None)
        application = AffiliateApplication.objects.create(**validated_data)
        order = 0
        for row in getattr(self, '_proof_url_rows', []):
            AffiliateProofAttachment.objects.create(
                application=application,
                label=row['label'],
                url=row['url'],
                sort_order=order,
            )
            order += 1
        for label, f in getattr(self, '_proof_file_pairs', []):
            AffiliateProofAttachment.objects.create(
                application=application,
                label=label,
                file=f,
                sort_order=order,
            )
            order += 1
        return application
