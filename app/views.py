"""Public resident profile - QR scanner app and API (no login required)."""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from operations.models import Resident


def resident_profile_pdf(request, pk):
    """Generate and return resident profile PDF matching Profiling-template layout fields."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    resident = get_object_or_404(Resident, pk=pk)
    response = HttpResponse(content_type='application/pdf')
    filename = f"resident_profile_{resident.resident_id or resident.id}.pdf"
    response['Content-Disposition'] = f'attachment; filename=\"{filename}\"'

    buffer = response
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=10,
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
    )

    elements = []
    elements.append(Paragraph("PPS Palawan Profiling System", title_style))
    elements.append(Spacer(1, 0.15 * inch))

    # Name line (similar to LASTNAME, FIRSTNAME in template)
    full_name = resident.get_full_name()
    elements.append(Paragraph(f"<b>{full_name}</b>", body_style))
    elements.append(Spacer(1, 0.1 * inch))

    # Birthdate, Age, Gender, Contact No (single line, as in docx template)
    birthdate_str = resident.date_of_birth.strftime('%b-%d-%Y') if resident.date_of_birth else '—'
    age_val = resident.get_age() if resident.date_of_birth else ''
    age_str = f"{age_val}" if age_val else '—'
    gender_str = resident.get_gender_display()
    contact_str = resident.contact_no or '—'
    line1 = (
        f"<b>Birthdate:</b> {birthdate_str}&nbsp;&nbsp;  "
        f"<b>Age:</b> {age_str}&nbsp;&nbsp;  "
        f"<b>Gender:</b> {gender_str}&nbsp;&nbsp;  "
        f"<b>Contact No:</b> {contact_str}"
    )
    elements.append(Paragraph(line1, body_style))

    # Address line
    addr = resident.address or '—'
    if resident.purok:
        addr = f"{addr}, {resident.purok}"
    elements.append(Paragraph(f"<b>Address:</b> {addr}", body_style))

    # PWD / SENIOR / VOTERS badges (from template wording)
    badges = []
    if resident.health_status == 'PWD':
        badges.append('PWD')
    if resident.economic_status == 'SENIOR CITIZEN':
        badges.append('SENIOR')
    if getattr(resident, 'is_voter', False):
        badges.append('VOTERS')
    badges_str = ', '.join(badges) if badges else '—'
    elements.append(Paragraph(f"<b>Remarks:</b> {badges_str}", body_style))

    doc.build(elements)
    return response


def app_info(request):
    """Info page - use the PPS app on your phone. Redirect ?res=id to profiling page."""
    res_id = request.GET.get('res')
    if res_id:
        return redirect('app:resident_profile', pk=res_id)
    return render(request, 'app/info.html')


def residents_search_api(request):
    """Public API: search residents by name or ID (for scanner app)."""
    q = (request.GET.get('q') or '').strip()
    if not q or len(q) < 2:
        return JsonResponse({'results': []})
    qs = Resident.objects.filter(
        Q(firstname__icontains=q) | Q(lastname__icontains=q) | Q(middlename__icontains=q)
        | Q(resident_id__icontains=q)
    ).select_related('barangay')[:30]
    results = [
        {
            'id': r.id,
            'resident_id': r.resident_id or '',
            'full_name': r.get_full_name(),
            'barangay': r.barangay.name if r.barangay else '',
        }
        for r in qs
    ]
    return JsonResponse({'results': results})


def _resident_profile_url(resident, request):
    """Profile image URL: Supabase Storage or Django media."""
    if resident.profile_picture_url:
        return resident.profile_picture_url
    if resident.profile_picture:
        try:
            return request.build_absolute_uri(resident.profile_picture.url)
        except Exception:
            pass
    return ''


def resident_api(request, pk):
    """Public API: resident data as JSON (for scanner app)."""
    resident = get_object_or_404(Resident, pk=pk)
    profile_url = _resident_profile_url(resident, request)
    pdf_url = request.build_absolute_uri(f'/app/resident/{pk}/pdf/')
    date_of_birth_str = resident.date_of_birth.strftime('%Y-%m-%d') if resident.date_of_birth else ''
    data = {
        'id': resident.id,
        'resident_id': resident.resident_id or '',
        'full_name': resident.get_full_name(),
        'profile_picture': profile_url,
        'contact_no': resident.contact_no or '',
        'gender': resident.get_gender_display(),
        'status': resident.get_status_display(),
        'date_of_birth': date_of_birth_str,
        'age': resident.get_age(),
        'place_of_birth': resident.place_of_birth or '',
        'address': resident.address or '',
        'purok': resident.purok or '',
        'barangay': resident.barangay.name if resident.barangay else '',
        'civil_status': resident.get_civil_status_display(),
        'occupation': resident.occupation or '',
        'citizenship': resident.citizenship or '',
        'educational_attainment': resident.get_educational_attainment_display(),
        'health_status': resident.get_health_status_display(),
        'economic_status': resident.get_economic_status_display(),
        'remarks': resident.remarks or '',
        'pdf_url': pdf_url,
    }
    return JsonResponse(data)


def resident_profile(request, pk):
    """Show profiling template when QR is scanned (profile picture, barangay, QR, economic status)."""
    resident = get_object_or_404(Resident, pk=pk)
    profile_picture_url = _resident_profile_url(resident, request)
    return render(request, 'app/profiling.html', {
        'resident': resident,
        'profile_picture_url': profile_picture_url,
    })
