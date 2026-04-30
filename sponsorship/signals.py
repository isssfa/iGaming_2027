from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Sponsorship
from sponsor.models import Sponsor


@receiver(m2m_changed, sender=Sponsor.sponsorship_package.through)
def update_total_sold(sender, instance, action, pk_set, **kwargs):
    """
    Signal handler to automatically update total_sold when sponsors are
    attached or removed from sponsorship packages.
    
    When a Sponsor instance is modified:
    - instance: The Sponsor instance being modified
    - pk_set: Set of Sponsorship primary keys being added/removed
    - action: 'pre_add', 'post_add', 'pre_remove', 'post_remove', 'pre_clear', 'post_clear'
    """
    if action in ('post_add', 'post_remove', 'post_clear'):
        # Update total_sold for all affected sponsorship packages
        if action == 'post_clear':
            # When all sponsors are cleared, update all sponsorship packages
            # that were previously associated with this sponsor
            if isinstance(instance, Sponsor):
                # Get all sponsorship packages that had this sponsor
                affected_sponsorships = Sponsorship.objects.filter(sponsors=instance)
                for sponsorship in affected_sponsorships:
                    sponsorship.total_sold = sponsorship.sponsors.count()
                    sponsorship.save(update_fields=['total_sold'])
        else:
            # For post_add and post_remove, pk_set contains the sponsorship IDs
            for sponsorship_id in pk_set:
                try:
                    sponsorship = Sponsorship.objects.get(pk=sponsorship_id)
                    # Count the number of sponsors currently associated with this package
                    sponsorship.total_sold = sponsorship.sponsors.count()
                    sponsorship.save(update_fields=['total_sold'])
                except Sponsorship.DoesNotExist:
                    pass

