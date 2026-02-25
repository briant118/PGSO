from django.db import models
from django.conf import settings


class UserProfile(models.Model):
    """
    Per-user permission overrides. Staff users cannot delete by default;
    these flags unrestrict delete in Operations and/or Reference.
    Admin role can delete everywhere regardless.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='userprofile'
    )
    can_delete_in_operations = models.BooleanField(
        default=False,
        help_text='Allow this user to delete records in Operations (Coordinator, Barangay Officials, Residents, etc.)'
    )
    can_delete_in_reference = models.BooleanField(
        default=False,
        help_text='Allow this user to delete records in Reference (Barangay, Positions, etc.)'
    )

    class Meta:
        verbose_name = 'User profile'
        verbose_name_plural = 'User profiles'

    def __str__(self):
        return f'Permissions for {self.user.username}'


class UserActivity(models.Model):
    """Log of user actions (login, logout, etc.) for the User Activity page."""
    ACTION_LOGIN = 'login'
    ACTION_LOGOUT = 'logout'
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_CHOICES = [
        (ACTION_LOGIN, 'Login'),
        (ACTION_LOGOUT, 'Logout'),
        (ACTION_CREATE, 'Create'),
        (ACTION_UPDATE, 'Update'),
        (ACTION_DELETE, 'Delete'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activity_logs',
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User activity'
        verbose_name_plural = 'User activities'

    def __str__(self):
        return f'{self.get_action_display()} by {self.user_id} at {self.created_at}'
