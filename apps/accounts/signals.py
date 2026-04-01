from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import AgentProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_agent_profile(sender, instance, created, **kwargs):
    if created:
        AgentProfile.objects.get_or_create(user=instance)
