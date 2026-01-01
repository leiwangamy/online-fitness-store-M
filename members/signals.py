# members/signals.py
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import MemberProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_member_profile(sender, instance, created, **kwargs):
    if created:
         # create profile here (adjust model name) - use get_or_create to avoid duplicates
        MemberProfile.objects.get_or_create(user=instance)
