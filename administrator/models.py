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

    # Granular manage permissions – control add/edit/delete per section.
    # If no manage flags are set for an area, staff retain full access there
    # (backwards compatible). Once any flag is enabled, only the checked
    # sections for that area may be modified.
    can_manage_reference = models.BooleanField(
        default=False,
        help_text='Allow managing all Reference sections (Barangay and Positions).'
    )
    can_manage_reference_barangay = models.BooleanField(
        default=False,
        help_text='Allow managing Barangay under Reference (add, edit, delete).'
    )
    can_manage_reference_position = models.BooleanField(
        default=False,
        help_text='Allow managing Position under Reference (add, edit, delete).'
    )

    can_manage_operations = models.BooleanField(
        default=False,
        help_text='Allow managing all Operations sections (Coordinator, Barangay Officials, Residents, Voters).'
    )
    can_manage_operations_coordinator = models.BooleanField(
        default=False,
        help_text='Allow managing Coordinator records (add, edit, delete).'
    )
    can_manage_operations_barangay_official = models.BooleanField(
        default=False,
        help_text='Allow managing Barangay Officials (add, edit, delete).'
    )
    can_manage_operations_residents_record = models.BooleanField(
        default=False,
        help_text='Allow managing Residents Record (add, edit, delete).'
    )
    can_manage_operations_voters_registration = models.BooleanField(
        default=False,
        help_text='Allow managing via Voters Registration screen (edit voter info).'
    )

    # Optional fine-grained action permissions per subsection.
    # These allow restricting a user to Add only, Edit only, or Delete only.
    # Main toggles above still grant full access when enabled.

    # Reference → Barangay
    can_add_reference_barangay = models.BooleanField(default=False)
    can_edit_reference_barangay = models.BooleanField(default=False)
    can_delete_reference_barangay = models.BooleanField(default=False)

    # Reference → Position
    can_add_reference_position = models.BooleanField(default=False)
    can_edit_reference_position = models.BooleanField(default=False)
    can_delete_reference_position = models.BooleanField(default=False)

    # Operations → Coordinator
    can_add_operations_coordinator = models.BooleanField(default=False)
    can_edit_operations_coordinator = models.BooleanField(default=False)
    can_delete_operations_coordinator = models.BooleanField(default=False)

    # Operations → Barangay Official
    can_add_operations_barangay_official = models.BooleanField(default=False)
    can_edit_operations_barangay_official = models.BooleanField(default=False)
    can_delete_operations_barangay_official = models.BooleanField(default=False)

    # Operations → Residents Record
    can_add_operations_residents_record = models.BooleanField(default=False)
    can_edit_operations_residents_record = models.BooleanField(default=False)
    can_delete_operations_residents_record = models.BooleanField(default=False)

    # Operations → Voters Registration
    can_add_operations_voters_registration = models.BooleanField(default=False)
    can_edit_operations_voters_registration = models.BooleanField(default=False)
    can_delete_operations_voters_registration = models.BooleanField(default=False)

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


class PasswordChangeRequest(models.Model):
    """User requests password change. Admin confirms, then new password is sent to user's email."""
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='password_change_requests',
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    processed_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True, help_text='When admin viewed this request')
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_password_requests',
    )

    class Meta:
        ordering = ['-requested_at']
        verbose_name = 'Password change request'
        verbose_name_plural = 'Password change requests'

    def __str__(self):
        return f'{self.user.username} – {self.get_status_display()}'


class SentEmail(models.Model):
    """Log of emails sent by the system (e.g. password change notifications)."""
    TYPE_PASSWORD_CHANGE = 'password_change'
    TYPE_PASSWORD_RESET = 'password_reset'
    TYPE_OTHER = 'other'
    TYPE_CHOICES = [
        (TYPE_PASSWORD_CHANGE, 'Password Change'),
        (TYPE_PASSWORD_RESET, 'Password Reset'),
        (TYPE_OTHER, 'Other'),
    ]

    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    body_plain = models.TextField(blank=True)
    email_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default=TYPE_OTHER)
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_emails',
    )
    related_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emails_received',
        help_text='User this email was about (e.g. user whose password was changed)',
    )

    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Sent email'
        verbose_name_plural = 'Sent emails'

    def __str__(self):
        return f'{self.subject} to {self.recipient_email} at {self.sent_at}'
