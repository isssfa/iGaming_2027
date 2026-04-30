# your_app_name/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db.models import Q # For complex lookups

from .models import Sponsorship
from .serializers import SponsorshipSerializer

class SponsorshipListAPIView(APIView):
    # Public endpoint - no authentication required
    permission_classes = [AllowAny]
    """
    API endpoint to retrieve a list of sponsorship packages.
    Supports filtering by id, title (case-insensitive contains), price (exact), and status (exact).
    """
    def get(self, request, *args, **kwargs):
        # Start with all Sponsorship objects
        queryset = Sponsorship.objects.all()

        # Get filter parameters from query params
        sponsorship_id = request.data.get('id', None)
        sponsorship_title = request.data.get('title', None)
        sponsorship_price = request.data.get('price', None)
        sponsorship_status = request.data.get('status', None)

        # Apply filters if provided
        if sponsorship_id:
            # For ID, ensure it's an integer for exact lookup
            try:
                sponsorship_id = int(sponsorship_id)
                queryset = queryset.filter(id=sponsorship_id)
            except ValueError:
                return Response(
                    {"detail": "Invalid 'id' parameter. Must be an integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if sponsorship_title:
            queryset = queryset.filter(title__icontains=sponsorship_title) # Case-insensitive contains

        if sponsorship_price:
            queryset = queryset.filter(price__exact=sponsorship_price) # Exact match for price string

        if sponsorship_status:
            # Ensure the status matches one of the defined choices, case-insensitive
            # You might want to validate this against the actual choices
            valid_statuses = [choice[0] for choice in Sponsorship.STATUS_CHOICES] # Get list of actual values
            if sponsorship_status.upper() in valid_statuses:
                 queryset = queryset.filter(status__iexact=sponsorship_status) # Case-insensitive exact match
            else:
                return Response(
                    {"detail": f"Invalid 'status' parameter. Must be one of {', '.join(valid_statuses)}."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Order the results, for example, by title or price
        queryset = queryset.order_by('id')

        # Serialize the filtered queryset
        # Pass request context for image URL generation
        serializer = SponsorshipSerializer(queryset, many=True, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)