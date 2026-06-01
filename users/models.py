

# Create your models here.

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.IntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)  # in kg
    height = models.FloatField(null=True, blank=True)  # in cm
    goal = models.CharField(max_length=100, blank=True)
    medical_conditions = models.TextField(blank=True)

    def __str__(self):
        return self.user.username

# Auto create profile when user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()