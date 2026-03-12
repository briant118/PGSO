from django.shortcuts import render
from datetime import date

from operations.models import Resident
from django.db.models import Count, Prefetch, Q
from django.utils import timezone
from reference.models import Barangay, Municipality
from django.urls import reverse


def reports_index(request):
    """Reports index view"""
    return render(request, 'reports/reports_index.html')


def _get_selected_year(request):
    """Read an optional `year` query param and return int or None."""
    year_raw = request.GET.get('year')
    if not year_raw:
        return None
    try:
        year = int(str(year_raw).strip())
    except (TypeError, ValueError):
        return None
    if year < 1900 or year > 3000:
        return None
    return year


def _get_selected_month(request):
    """Read an optional `month` query param (1-12) and return int or None."""
    month_raw = request.GET.get('month')
    if not month_raw:
        return None
    try:
        month = int(str(month_raw).strip())
    except (TypeError, ValueError):
        return None
    if month < 1 or month > 12:
        return None
    return month


def _available_years_for_queryset(qs):
    """
    Return list of year ints available in qs based on Resident.created_at.
    Works for DateTimeField (created_at).
    """
    years = [d.year for d in qs.datetimes('created_at', 'year', order='DESC')]
    current_year = timezone.now().year
    if current_year not in years:
        years.insert(0, current_year)
    # ensure unique, keep order (DESC with current year at front)
    seen = set()
    out = []
    for y in years:
        if y in seen:
            continue
        seen.add(y)
        out.append(y)
    return out


def _sidebar_municipalities_for_report(resident_rel_q: Q):
    """
    Build municipalities -> barangays tree with a `report_count` annotation on each barangay.

    `resident_rel_q` must be written against the Barangay->Resident reverse relation, e.g.
    Q(residents__status=..., residents__gender=...).
    """
    barangays_with_counts = (
        Barangay.objects.filter(is_active=True)
        .annotate(report_count=Count('residents', filter=resident_rel_q, distinct=True))
        .order_by('name')
    )
    return (
        Municipality.objects.filter(is_active=True)
        .prefetch_related(Prefetch('barangays', queryset=barangays_with_counts))
        .order_by('name')
    )


def _get_selected_barangay(request):
    barangay_id = request.GET.get('barangay')
    if not barangay_id:
        return None, None
    try:
        return Barangay.objects.select_related('municipality').get(pk=barangay_id), str(barangay_id)
    except Barangay.DoesNotExist:
        return None, None


def list_male(request):
    """List of male residents"""
    selected_barangay, selected_barangay_id = _get_selected_barangay(request)
    selected_year = _get_selected_year(request)
    base_qs = Resident.objects.filter(
        status=Resident.STATUS_ALIVE,
        gender=Resident.GENDER_MALE
    ).select_related('barangay').order_by('lastname', 'firstname')

    available_years = _available_years_for_queryset(base_qs)
    residents_qs = base_qs
    if selected_year:
        residents_qs = residents_qs.filter(created_at__year=selected_year)
    if selected_barangay:
        residents_qs = residents_qs.filter(barangay=selected_barangay)
    residents = residents_qs

    rel_q = Q(residents__status=Resident.STATUS_ALIVE, residents__gender=Resident.GENDER_MALE)
    if selected_year:
        rel_q &= Q(residents__created_at__year=selected_year)
    context = {
        'residents': residents,
        'count': residents.count(),
        'barangay': selected_barangay,
        'selected_barangay_id': selected_barangay_id,
        'municipalities': _sidebar_municipalities_for_report(rel_q),
        'base_path': request.path,
        'print_path': reverse('reports:print_male'),
        'available_years': available_years,
        'selected_year': selected_year,
    }
    return render(request, 'reports/list_male.html', context)


def list_female(request):
    """List of female residents"""
    selected_barangay, selected_barangay_id = _get_selected_barangay(request)
    selected_year = _get_selected_year(request)
    base_qs = Resident.objects.filter(
        status=Resident.STATUS_ALIVE,
        gender=Resident.GENDER_FEMALE
    ).select_related('barangay').order_by('lastname', 'firstname')

    available_years = _available_years_for_queryset(base_qs)
    residents_qs = base_qs
    if selected_year:
        residents_qs = residents_qs.filter(created_at__year=selected_year)
    if selected_barangay:
        residents_qs = residents_qs.filter(barangay=selected_barangay)
    residents = residents_qs

    rel_q = Q(residents__status=Resident.STATUS_ALIVE, residents__gender=Resident.GENDER_FEMALE)
    if selected_year:
        rel_q &= Q(residents__created_at__year=selected_year)
    context = {
        'residents': residents,
        'count': residents.count(),
        'barangay': selected_barangay,
        'selected_barangay_id': selected_barangay_id,
        'municipalities': _sidebar_municipalities_for_report(rel_q),
        'base_path': request.path,
        'print_path': reverse('reports:print_female'),
        'available_years': available_years,
        'selected_year': selected_year,
    }
    return render(request, 'reports/list_female.html', context)


def list_pwd(request):
    """List of PWD (Persons with Disabilities)"""
    selected_barangay, selected_barangay_id = _get_selected_barangay(request)
    selected_year = _get_selected_year(request)
    base_qs = Resident.objects.filter(
        status=Resident.STATUS_ALIVE,
        health_status='PWD'
    ).select_related('barangay').order_by('lastname', 'firstname')

    available_years = _available_years_for_queryset(base_qs)
    residents_qs = base_qs
    if selected_year:
        residents_qs = residents_qs.filter(created_at__year=selected_year)
    if selected_barangay:
        residents_qs = residents_qs.filter(barangay=selected_barangay)
    residents = residents_qs

    rel_q = Q(residents__status=Resident.STATUS_ALIVE, residents__health_status='PWD')
    if selected_year:
        rel_q &= Q(residents__created_at__year=selected_year)
    context = {
        'residents': residents,
        'count': residents.count(),
        'barangay': selected_barangay,
        'selected_barangay_id': selected_barangay_id,
        'municipalities': _sidebar_municipalities_for_report(rel_q),
        'base_path': request.path,
        'print_path': reverse('reports:print_pwd'),
        'available_years': available_years,
        'selected_year': selected_year,
    }
    return render(request, 'reports/list_pwd.html', context)


def list_solo_parent(request):
    """List of solo parents"""
    selected_barangay, selected_barangay_id = _get_selected_barangay(request)
    selected_year = _get_selected_year(request)
    base_qs = Resident.objects.filter(
        status=Resident.STATUS_ALIVE,
        economic_status='SOLO PARENT'
    ).select_related('barangay').order_by('lastname', 'firstname')

    available_years = _available_years_for_queryset(base_qs)
    residents_qs = base_qs
    if selected_year:
        residents_qs = residents_qs.filter(created_at__year=selected_year)
    if selected_barangay:
        residents_qs = residents_qs.filter(barangay=selected_barangay)
    residents = residents_qs

    rel_q = Q(residents__status=Resident.STATUS_ALIVE, residents__economic_status='SOLO PARENT')
    if selected_year:
        rel_q &= Q(residents__created_at__year=selected_year)
    context = {
        'residents': residents,
        'count': residents.count(),
        'barangay': selected_barangay,
        'selected_barangay_id': selected_barangay_id,
        'municipalities': _sidebar_municipalities_for_report(rel_q),
        'base_path': request.path,
        'print_path': reverse('reports:print_solo_parent'),
        'available_years': available_years,
        'selected_year': selected_year,
    }
    return render(request, 'reports/list_solo_parent.html', context)


def list_senior_citizen(request):
    """List of senior citizens"""
    selected_barangay, selected_barangay_id = _get_selected_barangay(request)
    selected_year = _get_selected_year(request)
    base_qs = Resident.objects.filter(
        status=Resident.STATUS_ALIVE,
        economic_status='SENIOR CITIZEN'
    ).select_related('barangay').order_by('lastname', 'firstname')

    available_years = _available_years_for_queryset(base_qs)
    residents_qs = base_qs
    if selected_year:
        residents_qs = residents_qs.filter(created_at__year=selected_year)
    if selected_barangay:
        residents_qs = residents_qs.filter(barangay=selected_barangay)
    residents = residents_qs

    rel_q = Q(residents__status=Resident.STATUS_ALIVE, residents__economic_status='SENIOR CITIZEN')
    if selected_year:
        rel_q &= Q(residents__created_at__year=selected_year)
    context = {
        'residents': residents,
        'count': residents.count(),
        'barangay': selected_barangay,
        'selected_barangay_id': selected_barangay_id,
        'municipalities': _sidebar_municipalities_for_report(rel_q),
        'base_path': request.path,
        'print_path': reverse('reports:print_senior_citizen'),
        'available_years': available_years,
        'selected_year': selected_year,
    }
    return render(request, 'reports/list_senior_citizen.html', context)


def list_4ps_member(request):
    """List of 4PS members"""
    selected_barangay, selected_barangay_id = _get_selected_barangay(request)
    selected_year = _get_selected_year(request)
    base_qs = Resident.objects.filter(
        status=Resident.STATUS_ALIVE,
        economic_status='4PS MEMBER'
    ).select_related('barangay').order_by('lastname', 'firstname')

    available_years = _available_years_for_queryset(base_qs)
    residents_qs = base_qs
    if selected_year:
        residents_qs = residents_qs.filter(created_at__year=selected_year)
    if selected_barangay:
        residents_qs = residents_qs.filter(barangay=selected_barangay)
    residents = residents_qs

    rel_q = Q(residents__status=Resident.STATUS_ALIVE, residents__economic_status='4PS MEMBER')
    if selected_year:
        rel_q &= Q(residents__created_at__year=selected_year)
    context = {
        'residents': residents,
        'count': residents.count(),
        'barangay': selected_barangay,
        'selected_barangay_id': selected_barangay_id,
        'municipalities': _sidebar_municipalities_for_report(rel_q),
        'base_path': request.path,
        'print_path': reverse('reports:print_4ps_member'),
        'available_years': available_years,
        'selected_year': selected_year,
    }
    return render(request, 'reports/list_4ps_member.html', context)


def list_voters(request):
    """List of voters, optionally filtered by barangay."""
    selected_barangay, selected_barangay_id = _get_selected_barangay(request)
    selected_year = _get_selected_year(request)

    base_qs = Resident.objects.filter(
        status=Resident.STATUS_ALIVE,
        is_voter=True,
    )

    available_years = _available_years_for_queryset(base_qs)
    residents_qs = base_qs
    if selected_year:
        residents_qs = residents_qs.filter(created_at__year=selected_year)
    if selected_barangay:
        residents_qs = residents_qs.filter(barangay=selected_barangay)

    residents = (
        residents_qs.select_related('barangay')
        .order_by('lastname', 'firstname')
    )

    rel_q = Q(residents__status=Resident.STATUS_ALIVE, residents__is_voter=True)
    if selected_year:
        rel_q &= Q(residents__created_at__year=selected_year)
    context = {
        'residents': residents,
        'count': residents.count(),
        'barangay': selected_barangay,
        'selected_barangay_id': selected_barangay_id,
        'municipalities': _sidebar_municipalities_for_report(rel_q),
        'base_path': request.path,
        'print_path': reverse('reports:print_voters'),
        'available_years': available_years,
        'selected_year': selected_year,
    }
    return render(request, 'reports/list_voters.html', context)


def list_residents_record(request):
    """List of all resident's records, optionally filtered by barangay."""
    selected_barangay, selected_barangay_id = _get_selected_barangay(request)
    selected_year = _get_selected_year(request)

    base_qs = Resident.objects.filter(
        status=Resident.STATUS_ALIVE,
    )

    available_years = _available_years_for_queryset(base_qs)
    residents_qs = base_qs
    if selected_year:
        residents_qs = residents_qs.filter(created_at__year=selected_year)
    if selected_barangay:
        residents_qs = residents_qs.filter(barangay=selected_barangay)

    residents = (
        residents_qs.select_related('barangay')
        .order_by('lastname', 'firstname')
    )

    rel_q = Q(residents__status=Resident.STATUS_ALIVE)
    if selected_year:
        rel_q &= Q(residents__created_at__year=selected_year)
    context = {
        'residents': residents,
        'count': residents.count(),
        'barangay': selected_barangay,
        'selected_barangay_id': selected_barangay_id,
        'municipalities': _sidebar_municipalities_for_report(rel_q),
        'base_path': request.path,
        'print_path': reverse('reports:print_residents_record'),
        'available_years': available_years,
        'selected_year': selected_year,
    }
    return render(request, 'reports/list_residents_record.html', context)


def print_residents_record(request):
    """Printable list of residents (all or per barangay)."""
    return _render_print_resident_report(
        request,
        title="Residents Record",
        base_qs=Resident.objects.filter(status=Resident.STATUS_ALIVE),
    )


def print_deceased(request):
    """Printable list of deceased residents (all or per barangay).

    Year/Month filters are based on date_of_birth (Birthdate) to match the on-screen report.
    """
    selected_barangay, selected_barangay_id = _get_selected_barangay(request)
    selected_year = _get_selected_year(request)
    selected_month = _get_selected_month(request)
    if not selected_year:
        selected_month = None

    residents_qs = Resident.objects.filter(status=Resident.STATUS_DECEASED)
    if selected_year:
        residents_qs = residents_qs.filter(date_of_birth__year=selected_year)
    if selected_month:
        residents_qs = residents_qs.filter(date_of_birth__month=selected_month)
    if selected_barangay:
        residents_qs = residents_qs.filter(barangay=selected_barangay)

    residents = residents_qs.select_related('barangay').order_by('id')
    context = {
        'report_title': 'List of Deceased',
        'residents': residents,
        'count': residents.count(),
        'barangay': selected_barangay,
        'selected_barangay_id': selected_barangay_id,
        'selected_year': selected_year,
        'selected_month': selected_month,
        'printed_at': timezone.localtime(timezone.now()),
    }
    return render(request, 'reports/print_residents_report.html', context)


def print_birth_by_year(request):
    """Printable birth-by-year report (all or per barangay)."""
    selected_barangay, selected_barangay_id = _get_selected_barangay(request)
    selected_year = _get_selected_year(request)

    residents_qs = Resident.objects.filter(status=Resident.STATUS_ALIVE)
    if selected_year:
        residents_qs = residents_qs.filter(date_of_birth__year=selected_year)
    if selected_barangay:
        residents_qs = residents_qs.filter(barangay=selected_barangay)

    residents = residents_qs.select_related('barangay').order_by('id')
    context = {
        'report_title': 'Birth By Year',
        'residents': residents,
        'count': residents.count(),
        'barangay': selected_barangay,
        'selected_barangay_id': selected_barangay_id,
        'selected_year': selected_year,
        'printed_at': timezone.localtime(timezone.now()),
    }
    return render(request, 'reports/print_residents_report.html', context)


def list_deceased(request):
    """List of deceased residents, optionally filtered by barangay.

    Year/Month filters are based on date_of_birth (Birthdate).
    """
    selected_barangay, selected_barangay_id = _get_selected_barangay(request)
    selected_year = _get_selected_year(request)
    selected_month = _get_selected_month(request)
    if not selected_year:
        selected_month = None

    base_qs = Resident.objects.filter(
        status=Resident.STATUS_DECEASED,
    )

    years_qs = base_qs.exclude(date_of_birth__isnull=True)
    available_years = [d.year for d in years_qs.dates('date_of_birth', 'year', order='DESC')]
    current_year = timezone.now().year
    if current_year not in available_years:
        available_years.insert(0, current_year)
    available_months = []
    if selected_year:
        month_dates = years_qs.filter(date_of_birth__year=selected_year).dates('date_of_birth', 'month', order='ASC')
        available_months = [d.month for d in month_dates]
    residents_qs = base_qs
    if selected_year:
        residents_qs = residents_qs.filter(date_of_birth__year=selected_year)
    if selected_month:
        residents_qs = residents_qs.filter(date_of_birth__month=selected_month)
    if selected_barangay:
        residents_qs = residents_qs.filter(barangay=selected_barangay)

    residents = (
        residents_qs.select_related('barangay')
        .order_by('date_of_birth', 'lastname', 'firstname')
    )

    rel_q = Q(residents__status=Resident.STATUS_DECEASED)
    if selected_year:
        rel_q &= Q(residents__date_of_birth__year=selected_year)
    if selected_month:
        rel_q &= Q(residents__date_of_birth__month=selected_month)
    context = {
        'residents': residents,
        'count': residents.count(),
        'barangay': selected_barangay,
        'selected_barangay_id': selected_barangay_id,
        'municipalities': _sidebar_municipalities_for_report(rel_q),
        'base_path': request.path,
        'print_path': reverse('reports:print_deceased'),
        'available_years': available_years,
        'selected_year': selected_year,
        'available_months': available_months,
        'selected_month': selected_month,
    }
    return render(request, 'reports/list_deceased.html', context)


def list_birth_by_year(request):
    """List of residents by birth year (date_of_birth), optionally filtered by barangay."""
    selected_barangay, selected_barangay_id = _get_selected_barangay(request)
    selected_year = _get_selected_year(request)

    base_qs = Resident.objects.filter(
        status=Resident.STATUS_ALIVE,
    )

    available_years = [d.year for d in base_qs.dates('date_of_birth', 'year', order='DESC')]
    current_year = timezone.now().year
    if current_year not in available_years:
        available_years.insert(0, current_year)

    residents_qs = base_qs.select_related('barangay').order_by('lastname', 'firstname')
    if selected_year:
        residents_qs = residents_qs.filter(date_of_birth__year=selected_year)
    if selected_barangay:
        residents_qs = residents_qs.filter(barangay=selected_barangay)

    residents = residents_qs

    rel_q = Q(residents__status=Resident.STATUS_ALIVE)
    if selected_year:
        rel_q &= Q(residents__date_of_birth__year=selected_year)

    context = {
        'residents': residents,
        'count': residents.count(),
        'barangay': selected_barangay,
        'selected_barangay_id': selected_barangay_id,
        'municipalities': _sidebar_municipalities_for_report(rel_q),
        'base_path': request.path,
        'print_path': reverse('reports:print_birth_by_year'),
        'available_years': available_years,
        'selected_year': selected_year,
    }
    return render(request, 'reports/list_birth_by_year.html', context)


def _render_print_resident_report(request, *, title: str, base_qs):
    selected_barangay, selected_barangay_id = _get_selected_barangay(request)
    selected_year = _get_selected_year(request)

    residents_qs = base_qs
    if selected_year:
        residents_qs = residents_qs.filter(created_at__year=selected_year)
    if selected_barangay:
        residents_qs = residents_qs.filter(barangay=selected_barangay)

    residents = residents_qs.select_related('barangay').order_by('id')
    context = {
        'report_title': title,
        'residents': residents,
        'count': residents.count(),
        'barangay': selected_barangay,
        'selected_barangay_id': selected_barangay_id,
        'selected_year': selected_year,
        'printed_at': timezone.localtime(timezone.now()),
    }
    return render(request, 'reports/print_residents_report.html', context)


def print_male(request):
    return _render_print_resident_report(
        request,
        title='List of Male',
        base_qs=Resident.objects.filter(status=Resident.STATUS_ALIVE, gender=Resident.GENDER_MALE),
    )


def print_female(request):
    return _render_print_resident_report(
        request,
        title='List of Female',
        base_qs=Resident.objects.filter(status=Resident.STATUS_ALIVE, gender=Resident.GENDER_FEMALE),
    )


def print_pwd(request):
    return _render_print_resident_report(
        request,
        title='List of PWD',
        base_qs=Resident.objects.filter(status=Resident.STATUS_ALIVE, health_status='PWD'),
    )


def print_solo_parent(request):
    return _render_print_resident_report(
        request,
        title='List of Solo Parent',
        base_qs=Resident.objects.filter(status=Resident.STATUS_ALIVE, economic_status='SOLO PARENT'),
    )


def print_senior_citizen(request):
    return _render_print_resident_report(
        request,
        title='List of Senior Citizen',
        base_qs=Resident.objects.filter(status=Resident.STATUS_ALIVE, economic_status='SENIOR CITIZEN'),
    )


def print_4ps_member(request):
    return _render_print_resident_report(
        request,
        title='List of 4PS Member',
        base_qs=Resident.objects.filter(status=Resident.STATUS_ALIVE, economic_status='4PS MEMBER'),
    )


def print_voters(request):
    return _render_print_resident_report(
        request,
        title='List of Voters',
        base_qs=Resident.objects.filter(status=Resident.STATUS_ALIVE, is_voter=True),
    )
