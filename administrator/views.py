from django.shortcuts import render


def administrator_index(request):
    """Administrator control index view"""
    return render(request, 'administrator/administrator_index.html')


def system_policy(request):
    """System policy management"""
    return render(request, 'administrator/system_policy.html')


def user_accounts(request):
    """User accounts management"""
    return render(request, 'administrator/user_accounts.html')


def user_activity(request):
    """User activity logs"""
    return render(request, 'administrator/user_activity.html')
