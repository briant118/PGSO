import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from django.db.models import Q, Count
from django.db.models.functions import TruncMonth, ExtractYear
from operations.models import Resident
from reference.models import Barangay, Municipality
from administrator.models import UserActivity
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

    # User activity filters (year, month)
    activity_year = None
    activity_month = None
    year_raw = request.GET.get('activity_year')
    month_raw = request.GET.get('activity_month')
    if year_raw:
        try:
            activity_year = int(str(year_raw).strip())
            if activity_year < 1900 or activity_year > 2100:
                activity_year = None
        except (TypeError, ValueError):
            pass
    if month_raw and activity_year:
        try:
            activity_month = int(str(month_raw).strip())
            if activity_month < 1 or activity_month > 12:
                activity_month = None
        except (TypeError, ValueError):
            pass

    activity_qs = UserActivity.objects.all()
    if activity_year:
        activity_qs = activity_qs.filter(created_at__year=activity_year)
    if activity_month:
        activity_qs = activity_qs.filter(created_at__month=activity_month)

    chart_data = _build_activity_chart_data(activity_qs)
    total_login = chart_data['totals']['login']
    total_logout = chart_data['totals']['logout']
    total_create = chart_data['totals']['create']
    total_update = chart_data['totals']['update']
    total_delete = chart_data['totals']['delete']
    chart_data_json = json.dumps({k: v for k, v in chart_data.items() if k != 'totals'})

    # Birth year chart: count residents by birth year
    by_birth_year = (
        Resident.objects
        .annotate(birth_year=ExtractYear('date_of_birth'))
        .values('birth_year')
        .annotate(count=Count('id'))
        .order_by('birth_year')
    )
    birth_year_map = {}
    current_year = today.year
    for row in by_birth_year:
        if row['birth_year']:
            birth_year_map[str(row['birth_year'])] = row['count']
    if str(current_year) not in birth_year_map:
        birth_year_map[str(current_year)] = 0
    birth_year_labels = sorted(birth_year_map.keys(), key=int)
    birth_year_counts = [birth_year_map[y] for y in birth_year_labels]

    birth_year_data = {
        'labels': birth_year_labels,
        'counts': birth_year_counts,
    }
    birth_year_data_json = json.dumps(birth_year_data)

    # Death year chart: count deceased residents by death year
    by_death_year = (
        Resident.objects
        .filter(status=Resident.STATUS_DECEASED, date_of_death__isnull=False)
        .annotate(death_year=ExtractYear('date_of_death'))
        .values('death_year')
        .annotate(count=Count('id'))
        .order_by('death_year')
    )
    death_year_map = {}
    for row in by_death_year:
        if row['death_year']:
            death_year_map[str(row['death_year'])] = row['count']
    if str(current_year) not in death_year_map:
        death_year_map[str(current_year)] = 0
    death_year_labels = sorted(death_year_map.keys(), key=int)
    death_year_counts = [death_year_map[y] for y in death_year_labels]

    death_year_data = {
        'labels': death_year_labels,
        'counts': death_year_counts,
    }
    death_year_data_json = json.dumps(death_year_data)

    # Barangays and municipalities totals for chart
    total_barangays = Barangay.objects.filter(is_active=True).count()
    total_municipalities = Municipality.objects.filter(is_active=True).count()
    bar_muni_chart_data = {
        'labels': ['Barangays', 'Municipalities'],
        'counts': [total_barangays, total_municipalities],
    }
    bar_muni_chart_json = json.dumps(bar_muni_chart_data)

    # Available years for activity filter (from UserActivity)
    activity_years = list(dict.fromkeys(
        [d.year for d in UserActivity.objects.dates('created_at', 'year', order='DESC')]
    ))
    if not activity_years or today.year not in activity_years:
        activity_years = [today.year] + [y for y in activity_years if y != today.year]

    return render(request, 'mainapplication/dashboard.html', {
        'stats': stats,
        'chart_data_json': chart_data_json,
        'chart_totals': {
            'login': total_login,
            'logout': total_logout,
            'create': total_create,
            'update': total_update,
            'delete': total_delete,
        },
        'activity_year': activity_year,
        'activity_month': activity_month,
        'activity_years': activity_years,
        'birth_year_data_json': birth_year_data_json,
        'death_year_data_json': death_year_data_json,
        'bar_muni_chart_json': bar_muni_chart_json,
    })


def _build_activity_chart_data(activity_qs):
    """Build chart data from UserActivity queryset."""
    by_month = (
        activity_qs
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(
            login=Count('id', filter=Q(action=UserActivity.ACTION_LOGIN)),
            logout=Count('id', filter=Q(action=UserActivity.ACTION_LOGOUT)),
            create=Count('id', filter=Q(action=UserActivity.ACTION_CREATE)),
            update=Count('id', filter=Q(action=UserActivity.ACTION_UPDATE)),
            delete=Count('id', filter=Q(action=UserActivity.ACTION_DELETE)),
        )
        .order_by('month')
    )
    chart_labels = []
    chart_login = []
    chart_logout = []
    chart_create = []
    chart_update = []
    chart_delete = []
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for row in by_month:
        if row['month']:
            chart_labels.append(f"{months[row['month'].month - 1]} {row['month'].year}")
            chart_login.append(row['login'])
            chart_logout.append(row['logout'])
            chart_create.append(row['create'])
            chart_update.append(row['update'])
            chart_delete.append(row['delete'])
    return {
        'labels': chart_labels,
        'login': chart_login,
        'logout': chart_logout,
        'create': chart_create,
        'update': chart_update,
        'delete': chart_delete,
        'totals': {
            'login': sum(chart_login),
            'logout': sum(chart_logout),
            'create': sum(chart_create),
            'update': sum(chart_update),
            'delete': sum(chart_delete),
        },
    }


@never_cache
@require_GET
def dashboard_activity_chart(request):
    """API: User activity chart data filtered by year/month."""
    activity_year = None
    activity_month = None
    year_raw = request.GET.get('activity_year')
    month_raw = request.GET.get('activity_month')
    if year_raw:
        try:
            activity_year = int(str(year_raw).strip())
            if activity_year < 1900 or activity_year > 2100:
                activity_year = None
        except (TypeError, ValueError):
            pass
    if month_raw and activity_year:
        try:
            activity_month = int(str(month_raw).strip())
            if activity_month < 1 or activity_month > 12:
                activity_month = None
        except (TypeError, ValueError):
            pass
    activity_qs = UserActivity.objects.all()
    if activity_year:
        activity_qs = activity_qs.filter(created_at__year=activity_year)
    if activity_month:
        activity_qs = activity_qs.filter(created_at__month=activity_month)
    data = _build_activity_chart_data(activity_qs)
    return JsonResponse(data)


@never_cache
@require_GET
def dashboard_birth_death_list(request):
    """API: List residents by birth or death year/month for dashboard modal."""
    list_type = request.GET.get('type', 'birth')  # 'birth' or 'death'
    year_raw = request.GET.get('year')
    month_raw = request.GET.get('month')

    year = None
    if year_raw:
        try:
            year = int(str(year_raw).strip())
            if year < 1900 or year > 3000:
                year = None
        except (TypeError, ValueError):
            pass

    month = None
    if month_raw:
        try:
            month = int(str(month_raw).strip())
            if month < 1 or month > 12:
                month = None
        except (TypeError, ValueError):
            pass
    if year is None:
        month = None

    if list_type == 'death':
        qs = Resident.objects.filter(
            status=Resident.STATUS_DECEASED,
            date_of_death__isnull=False,
        )
        if year:
            qs = qs.filter(date_of_death__year=year)
        if month:
            qs = qs.filter(date_of_death__month=month)
        qs = qs.select_related('barangay').order_by('date_of_death', 'lastname', 'firstname')
    else:
        qs = Resident.objects.all()
        if year:
            qs = qs.filter(date_of_birth__year=year)
        if month:
            qs = qs.filter(date_of_birth__month=month)
        qs = qs.select_related('barangay').order_by('date_of_birth', 'lastname', 'firstname')

    residents = []
    for r in qs[:500]:
        residents.append({
            'id': r.id,
            'resident_id': r.resident_id or '',
            'full_name': r.get_full_name(),
            'barangay': r.barangay.name if r.barangay else '',
            'date_of_birth': r.date_of_birth.strftime('%Y-%m-%d') if r.date_of_birth else '',
            'date_of_death': r.date_of_death.strftime('%Y-%m-%d') if r.date_of_death else '',
            'status': r.status or 'ALIVE',
        })

    return JsonResponse({'residents': residents, 'count': len(residents)})

