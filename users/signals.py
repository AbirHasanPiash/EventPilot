from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile


@receiver(post_save, sender=User)
def create_user_profile_after_activation(sender, instance, created, **kwargs):
    """
    Create UserProfile only when user is verified (is_active=True)
    and profile doesn't exist.
    """
    if instance.is_active and not hasattr(instance, 'profile'):
        UserProfile.objects.get_or_create(user=instance)
