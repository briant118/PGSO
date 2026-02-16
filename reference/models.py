from django.db import models


class Municipality(models.Model):
    """Reference data for municipalities."""
    name = models.CharField(max_length=100, unique=True)
    province = models.CharField(max_length=100, default='Palawan')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Municipalities'

    def __str__(self):
        return self.name


class Barangay(models.Model):
    """Reference data for barangays."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    municipality = models.ForeignKey(Municipality, on_delete=models.PROTECT, related_name='barangays', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Barangays'

    def __str__(self):
        return self.name


class Position(models.Model):
    """Reference data for positions."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Positions'

    def __str__(self):
        return self.name
