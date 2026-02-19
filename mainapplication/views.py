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

    # Stats chart: convert stat cards to chart data
    stats_chart_data = {
        'labels': [
            'Total Male',
            'Total Female',
            'Total Senior Citizen',
            'Total PWD',
            'Total Solo Parent',
            'Total Voters',
            'Total Residents Record',
            'Total 4P\'s Member'
        ],
        'counts': [
            stats['total_male'],
            stats['total_female'],
            stats['total_senior_citizen'],
            stats['total_pwd'],
            stats['total_solo_parent'],
            stats['total_voters'],
            stats['total_residents_record'],
            stats['total_4ps_member'],
        ],
        'colors': [
            'rgba(91, 192, 222, 0.8)',  # Light blue (male)
            'rgba(232, 62, 140, 0.8)',  # Pink/magenta (female)
            'rgba(40, 167, 69, 0.8)',   # Green (senior)
            'rgba(255, 193, 7, 0.8)',   # Yellow (PWD)
            'rgba(108, 117, 125, 0.8)', # Dark grey (solo parent)
            'rgba(253, 126, 20, 0.8)',  # Orange (voters)
            'rgba(0, 123, 255, 0.8)',   # Blue (residents)
            'rgba(111, 66, 193, 0.8)',  # Purple (4Ps)
        ],
        'borderColors': [
            'rgb(91, 192, 222)',
            'rgb(232, 62, 140)',
            'rgb(40, 167, 69)',
            'rgb(255, 193, 7)',
            'rgb(108, 117, 125)',
            'rgb(253, 126, 20)',
            'rgb(0, 123, 255)',
            'rgb(111, 66, 193)',
        ]
    }
    stats_chart_data_json = json.dumps(stats_chart_data)

    return render(request, 'mainapplication/dashboard.html', {
        'stats': stats,
        'chart_data_json': chart_data_json,
        'birth_year_data_json': birth_year_data_json,
        'stats_chart_data_json': stats_chart_data_json,
    })

