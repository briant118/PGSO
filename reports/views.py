from django.shortcuts import render
from datetime import date

from operations.models import Resident
from reference.models import Barangay


def reports_index(request):
    """Reports index view"""
    return render(request, 'reports/reports_index.html')


def list_male(request):
    """List of male residents"""
    residents = Resident.objects.filter(
        status=Resident.STATUS_ALIVE,
        gender=Resident.GENDER_MALE
    ).select_related('barangay').order_by('lastname', 'firstname')
    
    context = {
        'residents': residents,
        'count': residents.count()
    }
    return render(request, 'reports/list_male.html', context)


def list_female(request):
    """List of female residents"""
    residents = Resident.objects.filter(
        status=Resident.STATUS_ALIVE,
        gender=Resident.GENDER_FEMALE
    ).select_related('barangay').order_by('lastname', 'firstname')
    
    context = {
        'residents': residents,
        'count': residents.count()
    }
    return render(request, 'reports/list_female.html', context)


def list_pwd(request):
    """List of PWD (Persons with Disabilities)"""
    residents = Resident.objects.filter(
        status=Resident.STATUS_ALIVE,
        health_status='PWD'
    ).select_related('barangay').order_by('lastname', 'firstname')
    
    context = {
        'residents': residents,
        'count': residents.count()
    }
    return render(request, 'reports/list_pwd.html', context)


def list_solo_parent(request):
    """List of solo parents"""
    residents = Resident.objects.filter(
        status=Resident.STATUS_ALIVE,
        economic_status='SOLO PARENT'
    ).select_related('barangay').order_by('lastname', 'firstname')
    
    context = {
        'residents': residents,
        'count': residents.count()
    }
    return render(request, 'reports/list_solo_parent.html', context)


def list_senior_citizen(request):
    """List of senior citizens"""
    residents = Resident.objects.filter(
        status=Resident.STATUS_ALIVE,
        economic_status='SENIOR CITIZEN'
    ).select_related('barangay').order_by('lastname', 'firstname')
    
    context = {
        'residents': residents,
        'count': residents.count()
    }
    return render(request, 'reports/list_senior_citizen.html', context)


def list_4ps_member(request):
    """List of 4PS members"""
    residents = Resident.objects.filter(
        status=Resident.STATUS_ALIVE,
        economic_status='4PS MEMBER'
    ).select_related('barangay').order_by('lastname', 'firstname')
    
    context = {
        'residents': residents,
        'count': residents.count()
    }
    return render(request, 'reports/list_4ps_member.html', context)


def list_voters(request):
    """List of voters, optionally filtered by barangay."""
    barangay_id = request.GET.get('barangay')
    barangay = None

    residents_qs = Resident.objects.filter(
        status=Resident.STATUS_ALIVE,
        is_voter=True,
    )

    if barangay_id:
        try:
            barangay = Barangay.objects.get(pk=barangay_id)
            residents_qs = residents_qs.filter(barangay=barangay)
        except Barangay.DoesNotExist:
            barangay = None

    residents = (
        residents_qs.select_related('barangay')
        .order_by('lastname', 'firstname')
    )

    context = {
        'residents': residents,
        'count': residents.count(),
        'barangay': barangay,
    }
    return render(request, 'reports/list_voters.html', context)


def list_residents_record(request):
    """List of all resident's records, optionally filtered by barangay."""
    barangay_id = request.GET.get('barangay')
    barangay = None

    residents_qs = Resident.objects.filter(
        status=Resident.STATUS_ALIVE,
    )

    if barangay_id:
        try:
            barangay = Barangay.objects.get(pk=barangay_id)
            residents_qs = residents_qs.filter(barangay=barangay)
        except Barangay.DoesNotExist:
            barangay = None

    residents = (
        residents_qs.select_related('barangay')
        .order_by('lastname', 'firstname')
    )

    context = {
        'residents': residents,
        'count': residents.count(),
        'barangay': barangay,
    }
    return render(request, 'reports/list_residents_record.html', context)
