from django.core.management.base import BaseCommand
from security.models import APICSRFToken


class Command(BaseCommand):
    help = 'Clean up expired and used CSRF tokens (more aggressive cleanup - removes tokens older than 24 hours)'

    def handle(self, *args, **options):
        deleted_count = APICSRFToken.cleanup_expired_tokens()
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully cleaned up {deleted_count} expired/used CSRF tokens'
            )
        )

