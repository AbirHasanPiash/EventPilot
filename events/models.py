from django.db import models
from users.models import User
from cloudinary.models import CloudinaryField


class EventCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Event(models.Model):
    VISIBILITY_CHOICES = (
        ('public', 'Public'),
        ('private', 'Private'),
    )

    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled'),
    )

    organizer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='organized_events'
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(
        EventCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events'
    )
    tags = models.JSONField(default=list, blank=True)

    image = CloudinaryField('image', blank=True, null=True)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    venue = models.CharField(max_length=255, blank=True)
    location_map_url = models.URLField(blank=True)

    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')

    capacity = models.PositiveIntegerField(default=100)
    allow_waitlist = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_full(self):
        return self.capacity is not None and self.registrations.count() >= self.capacity

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ["-start_time"]
