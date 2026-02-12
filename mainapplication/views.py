from django.shortcuts import render


def dashboard(request):
    """Dashboard with stat cards. Counts can be wired to models when available."""
    # Placeholder counts; replace with model counts when resident/voter models exist
    stats = {
        'total_male': 0,
        'total_female': 0,
        'total_senior_citizen': 0,
        'total_pwd': 0,
        'total_solo_parent': 0,
        'total_voters': 0,
        'total_residents_record': 0,
        'total_4ps_member': 0,
    }
    return render(request, 'mainapplication/dashboard.html', {'stats': stats})

