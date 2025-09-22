from django.db import models
from django.conf import settings
from django.utils.timezone import now

class OrganizerRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='organizer_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.status}"
    
    def can_request_again(self):
        """Return (True, None) if can request again, else (False, days_remaining)"""
        if self.status == 'rejected' and self.reviewed_at:
            days_passed = (now() - self.reviewed_at).days
            if days_passed < 90:
                return False, 90 - days_passed
        return True, None