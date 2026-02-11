from django.shortcuts import render


def reports_index(request):
    """Reports index view"""
    return render(request, 'reports/reports_index.html')


def list_male(request):
    """List of male residents"""
    return render(request, 'reports/list_male.html')


def list_female(request):
    """List of female residents"""
    return render(request, 'reports/list_female.html')


def list_pwd(request):
    """List of PWD (Persons with Disabilities)"""
    return render(request, 'reports/list_pwd.html')


def list_solo_parent(request):
    """List of solo parents"""
    return render(request, 'reports/list_solo_parent.html')


def list_senior_citizen(request):
    """List of senior citizens"""
    return render(request, 'reports/list_senior_citizen.html')


def list_4ps_member(request):
    """List of 4PS members"""
    return render(request, 'reports/list_4ps_member.html')


def list_voters(request):
    """List of voters"""
    return render(request, 'reports/list_voters.html')


def list_residents_record(request):
    """List of resident's record"""
    return render(request, 'reports/list_residents_record.html')
