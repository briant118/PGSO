from django.shortcuts import render
from .models import Barangay, Position


def reference_index(request):
    """Reference landing page with links to Barangay and Positions."""
    return render(request, 'reference/reference_index.html')


def barangay_list(request):
    """List all active barangays."""
    barangays = Barangay.objects.filter(is_active=True)
    return render(request, 'reference/barangay_list.html', {'barangays': barangays})


def position_list(request):
    """List all active positions."""
    positions = Position.objects.filter(is_active=True)
    return render(request, 'reference/position_list.html', {'positions': positions})
