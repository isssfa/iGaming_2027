# your_app_name/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db.models import Q
from .models import Sponsor

from .serializers import SponsorDetailSerializer

class SponsorListAPIView(APIView):
    # Public endpoint - no authentication required
    permission_classes = [AllowAny]
    """
    API endpoint to retrieve sponsors grouped by type, with filtering by name and type.
    """
    def get(self, request, *args, **kwargs):
        # Get filter parameters from query params
        sponsor_name_filter = request.data.get('name', None)
        sponsor_type_filter = request.data.get('type', None) # New type filter

        # Start with all sponsors
        queryset = Sponsor.objects.all()

        # Apply name filter if provided
        if sponsor_name_filter:
            # Use Q object for case-insensitive contains lookup on name
            queryset = queryset.filter(Q(name__icontains=sponsor_name_filter))

        # Apply type filter if provided (New)
        if sponsor_type_filter:
            # Use Q object for exact match on type
            # Ensure the type matches one of your SPONSOR_TYPES choices (e.g., 'headline', 'platinum')
            queryset = queryset.filter(Q(type__iexact=sponsor_type_filter))


        # Initialize the dictionary for the final structured response
        grouped_sponsors = {
            "headlineSponsor": None, # Will hold a single object
            "diamondSponsors": [],
            "platinumSponsors": [],
            "goldSponsors": [],
            "silverSponsors": [],
            "bronzeSponsors": [],
            "mediaPartners": [],
            "strategicPartners": [],
            "attendingCompanies": [],
        }

        # Iterate through the filtered queryset and group sponsors
        # Order by type and then name for consistent output
        for sponsor in queryset.order_by('type', 'name'):
            serializer = SponsorDetailSerializer(sponsor, context={'request': request})
            sponsor_data = serializer.data

            # Grouping logic remains the same
            if sponsor.type == 'headline':
                if grouped_sponsors["headlineSponsor"] is None:
                    grouped_sponsors["headlineSponsor"] = sponsor_data
            elif sponsor.type == 'diamond':
                grouped_sponsors["diamondSponsors"].append(sponsor_data)
            elif sponsor.type == 'platinum':
                grouped_sponsors["platinumSponsors"].append(sponsor_data)
            elif sponsor.type == 'gold':
                grouped_sponsors["goldSponsors"].append(sponsor_data)
            elif sponsor.type == 'silver':
                grouped_sponsors["silverSponsors"].append(sponsor_data)
            elif sponsor.type == 'bronze':
                grouped_sponsors["bronzeSponsors"].append(sponsor_data)
            elif sponsor.type == 'strategic':
                grouped_sponsors["strategicPartners"].append(sponsor_data)
            elif sponsor.type == 'media':
                grouped_sponsors["mediaPartners"].append(sponsor_data)
            elif sponsor.type == 'attending_companies':
                grouped_sponsors["attendingCompanies"].append(sponsor_data)

        return Response(grouped_sponsors, status=status.HTTP_200_OK)

