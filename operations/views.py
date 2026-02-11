from django.shortcuts import render


def operations_index(request):
    return render(request, "operations/operations_index.html")


def coordinator(request):
    return render(request, "operations/coordinator.html")


def barangay_officials(request):
    return render(request, "operations/barangay_officials.html")


def residents_record(request):
    return render(request, "operations/residents_record.html")


def voters_registration(request):
    return render(request, "operations/voters_registration.html")
