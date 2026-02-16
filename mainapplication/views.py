from django.shortcuts import render
from django.db.models import Q
from operations.models import Resident
from datetime import date


def dashboard(request):
    """Dashboard with stat cards showing real-time resident data."""
    # Calculate age to determine senior citizens (60 years and older)
    today = date.today()
    
    # Get all alive residents
    alive_residents = Resident.objects.filter(status=Resident.STATUS_ALIVE)
    
    stats = {
        'total_male': alive_residents.filter(gender=Resident.GENDER_MALE).count(),
        'total_female': alive_residents.filter(gender=Resident.GENDER_FEMALE).count(),
        'total_senior_citizen': alive_residents.filter(economic_status='SENIOR CITIZEN').count(),
        'total_pwd': alive_residents.filter(health_status='PWD').count(),
        'total_solo_parent': alive_residents.filter(economic_status='SOLO PARENT').count(),
        'total_voters': alive_residents.filter(is_voter=True).count(),
        'total_residents_record': alive_residents.count(),
        'total_4ps_member': alive_residents.filter(economic_status='4PS MEMBER').count(),
    }
    return render(request, 'mainapplication/dashboard.html', {'stats': stats})

