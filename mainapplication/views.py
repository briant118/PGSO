from django.shortcuts import render


def dashboard(request):
    """Simple friendly dashboard with References (Barangay & Positions)."""
    return render(request, 'mainapplication/dashboard.html')

