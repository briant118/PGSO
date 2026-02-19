import json
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.db.models import Q, Count
from django.db.models.functions import TruncMonth, ExtractYear
from operations.models import Resident
from datetime import date


@never_cache
def dashboard(request):
    """Dashboard with stat cards showing real-time resident data."""
    today = date.today()
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
        'total_alive': Resident.objects.filter(status=Resident.STATUS_ALIVE).count(),
        'total_dead': Resident.objects.filter(status=Resident.STATUS_DECEASED).count(),
    }

    # Alive vs deceased by year and month (group by created_at month, count by current status)
    by_month = (
        Resident.objects
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(
            alive=Count('id', filter=Q(status=Resident.STATUS_ALIVE)),
            dead=Count('id', filter=Q(status=Resident.STATUS_DECEASED)),
        )
        .order_by('month')
    )
    chart_labels = []
    chart_alive = []
    chart_dead = []
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for row in by_month:
        if row['month']:
            chart_labels.append(f"{months[row['month'].month - 1]} {row['month'].year}")
            chart_alive.append(row['alive'])
            chart_dead.append(row['dead'])

    chart_data = {
        'labels': chart_labels,
        'alive': chart_alive,
        'dead': chart_dead,
    }
    chart_data_json = json.dumps(chart_data)

    # Birth year chart: count residents by birth year
    by_birth_year = (
        Resident.objects
        .annotate(birth_year=ExtractYear('date_of_birth'))
        .values('birth_year')
        .annotate(count=Count('id'))
        .order_by('birth_year')
    )
    birth_year_labels = []
    birth_year_counts = []
    for row in by_birth_year:
        if row['birth_year']:
            birth_year_labels.append(str(row['birth_year']))
            birth_year_counts.append(row['count'])

    birth_year_data = {
        'labels': birth_year_labels,
        'counts': birth_year_counts,
    }
    birth_year_data_json = json.dumps(birth_year_data)

    return render(request, 'mainapplication/dashboard.html', {
        'stats': stats,
        'chart_data_json': chart_data_json,
        'birth_year_data_json': birth_year_data_json,
    })

