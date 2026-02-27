from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models import Q, Count, Prefetch
from django.urls import reverse
from reference.models import Barangay, Municipality, Position
from administrator.utils import user_can_delete_in_operations
from administrator.activity_log import log_activity, ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE
from .models import Resident, BarangayOfficial, CoordinatorPosition, Coordinator
from django.conf import settings
import logging
import socket

# Set up logging
logger = logging.getLogger(__name__)


def _get_base_url_for_devices(request):
    """Return base URL reachable from other devices. Always includes http:// and :8000 for dev server."""
    site_url = getattr(settings, 'SITE_URL', '') or ''
    if site_url:
        base = site_url.strip().rstrip('/')
        if not base.startswith(('http://', 'https://')):
            base = 'http://' + base
        host_part = base.split('//')[-1].split('/')[0] if '//' in base else ''
        if host_part and ':' not in host_part:
            base = base.replace(host_part, host_part + ':8000', 1)
        return base
    host = request.get_host().split(':')[0]
    port = request.get_port() or '8000'
    if host in ('localhost', '127.0.0.1', ''):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.5)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return f'http://{ip}:{port}'
        except Exception:
            pass
    base = request.build_absolute_uri('/').rstrip('/')
    host_part = base.split('//')[-1].split('/')[0] if '//' in base else ''
    if host_part and ':' not in host_part:
        base = base.replace(host_part, host_part + ':8000', 1)
    return base


def operations_index(request):
    return render(request, "operations/operations_index.html")


def coordinator(request):
    """Coordinator page; positions are coordinator-only (CoordinatorPosition), not reference Position."""
    coordinator_positions = CoordinatorPosition.objects.filter(is_active=True).order_by('code')
    coordinator_positions_list = CoordinatorPosition.objects.all().order_by('code', 'name')
    coordinators = Coordinator.objects.select_related('barangay', 'position').all().order_by('barangay', 'fullname')
    search_query = request.GET.get('q', '').strip()
    if search_query:
        coordinators = coordinators.filter(
            Q(fullname__icontains=search_query)
            | Q(barangay__name__icontains=search_query)
            | Q(position__name__icontains=search_query)
            | Q(contact_no__icontains=search_query)
            | Q(remarks__icontains=search_query)
        )
    barangays = Barangay.objects.filter(is_active=True).order_by('name')
    context = {
        'coordinator_positions': coordinator_positions,
        'coordinator_positions_list': coordinator_positions_list,
        'coordinators': coordinators,
        'barangays': barangays,
        'search_query': search_query,
        'edit_pk': request.GET.get('edit'),
    }
    return render(request, "operations/coordinator.html", context)


def _fullname_matches_resident_in_barangay(barangay, fullname):
    """Return True if fullname matches an active resident in the barangay (case-insensitive)."""
    if not fullname or not barangay:
        return False
    residents = Resident.objects.filter(barangay=barangay, status=Resident.STATUS_ALIVE)
    fullname_clean = fullname.strip().lower()
    for r in residents:
        if r.get_full_name().strip().lower() == fullname_clean:
            return True
    return False


@transaction.atomic
def coordinator_add(request):
    """Create a new coordinator record."""
    if request.method == 'POST':
        fullname = request.POST.get('fullname', '').strip()
        if not fullname:
            messages.error(request, 'Fullname is required.')
            return redirect('operations:coordinator')
        barangay_id = request.POST.get('barangay')
        position_id = request.POST.get('position')
        if not barangay_id or not position_id:
            messages.error(request, 'Barangay and Position are required.')
            return redirect('operations:coordinator')
        barangay = get_object_or_404(Barangay, id=barangay_id)
        if not _fullname_matches_resident_in_barangay(barangay, fullname):
            messages.error(
                request,
                'The fullname must be a resident of the selected barangay. Please select a name from the list or enter a valid resident name.',
            )
            return redirect('operations:coordinator')
        position = get_object_or_404(CoordinatorPosition, id=position_id)
        contact_no = request.POST.get('contact_no', '').strip()
        if not contact_no:
            messages.error(request, 'Contact number is required.')
            return redirect('operations:coordinator')
        date_start_val = request.POST.get('date_start', '').strip()
        from datetime import datetime
        date_start = None
        if date_start_val:
            try:
                date_start = datetime.strptime(date_start_val, '%Y-%m-%d').date()
            except ValueError:
                pass
        Coordinator.objects.create(
            barangay=barangay,
            fullname=fullname,
            position=position,
            contact_no=contact_no,
            remarks=request.POST.get('remarks', ''),
            date_start=date_start,
            is_active=request.POST.get('is_active') == 'on',
        )
        log_activity(request, ACTION_CREATE, f'Added coordinator "{fullname}" ({position.name}, {barangay.name}).')
        messages.success(request, f'Coordinator "{fullname}" added successfully.')
    return redirect('operations:coordinator')


def coordinator_edit(request, pk):
    """Edit an existing coordinator. GET redirects to coordinator list and opens edit modal; POST saves."""
    obj = get_object_or_404(Coordinator, pk=pk)
    if request.method == 'GET':
        return redirect('operations:coordinator' + '?edit=' + str(pk))
    barangays = Barangay.objects.filter(is_active=True).order_by('name')
    coordinator_positions = CoordinatorPosition.objects.filter(is_active=True).order_by('code')
    if request.method == 'POST':
        fullname = request.POST.get('fullname', '').strip()
        if not fullname:
            messages.error(request, 'Fullname is required.')
            return redirect('operations:coordinator_edit', pk=pk)
        barangay_id = request.POST.get('barangay')
        position_id = request.POST.get('position')
        if not barangay_id or not position_id:
            messages.error(request, 'Barangay and Position are required.')
            return redirect('operations:coordinator_edit', pk=pk)
        barangay = get_object_or_404(Barangay, id=barangay_id)
        if not _fullname_matches_resident_in_barangay(barangay, fullname):
            messages.error(
                request,
                'The fullname must be a resident of the selected barangay. Please select a name from the list or enter a valid resident name.',
            )
            return redirect('operations:coordinator' + '?edit=' + str(pk))
        position = get_object_or_404(CoordinatorPosition, id=position_id)
        contact_no = request.POST.get('contact_no', '').strip()
        if not contact_no:
            messages.error(request, 'Contact number is required.')
            return redirect('operations:coordinator' + '?edit=' + str(pk))
        date_start_val = request.POST.get('date_start', '').strip()
        from datetime import datetime
        date_start = None
        if date_start_val:
            try:
                date_start = datetime.strptime(date_start_val, '%Y-%m-%d').date()
            except ValueError:
                pass
        obj.barangay = barangay
        obj.fullname = fullname
        obj.position = position
        obj.contact_no = contact_no
        obj.remarks = request.POST.get('remarks', '')
        obj.date_start = date_start
        obj.is_active = request.POST.get('is_active') == 'on'
        obj.save()
        log_activity(request, ACTION_UPDATE, f'Updated coordinator "{fullname}".')
        messages.success(request, f'Coordinator "{fullname}" updated successfully.')
        return redirect('operations:coordinator')
    return redirect('operations:coordinator')


def get_residents_by_barangay(request):
    """API endpoint to get residents by barangay with optional search."""
    barangay_id = request.GET.get('barangay_id')
    search = request.GET.get('search', '').strip()
    
    if not barangay_id:
        return JsonResponse({'residents': []}, safe=False)
    
    try:
        barangay = Barangay.objects.get(id=barangay_id, is_active=True)
        residents = Resident.objects.filter(barangay=barangay, status=Resident.STATUS_ALIVE)
        
        if search:
            words = [w.strip() for w in search.split() if w.strip()]
            if words:
                q = Q()
                for word in words:
                    q &= (
                        Q(firstname__icontains=word) |
                        Q(lastname__icontains=word) |
                        Q(middlename__icontains=word) |
                        Q(suffix__icontains=word)
                    )
                residents = residents.filter(q)
        
        residents = residents.order_by('lastname', 'firstname')[:50]  # Limit to 50 results
        
        official_resident_ids = set(
            BarangayOfficial.objects.filter(
                barangay=barangay, is_active=True
            ).values_list('resident_id', flat=True)
        )
        
        residents_data = [{
            'id': r.id,
            'fullname': r.get_full_name(),
            'firstname': r.firstname,
            'lastname': r.lastname,
            'middlename': r.middlename,
            'suffix': r.suffix,
            'is_already_official': r.id in official_resident_ids,
            'is_voter': r.is_voter,
        } for r in residents]
        
        return JsonResponse({'residents': residents_data}, safe=False)
    except Barangay.DoesNotExist:
        return JsonResponse({'residents': []}, safe=False)


def get_municipalities(request):
    """API endpoint to get municipalities with optional search."""
    search = request.GET.get('search', '').strip()
    municipalities_qs = Municipality.objects.filter(is_active=True).order_by('name')
    if search:
        municipalities_qs = municipalities_qs.filter(name__icontains=search)
    municipalities_qs = municipalities_qs[:100]
    data = [{'id': m.id, 'name': m.name} for m in municipalities_qs]
    return JsonResponse({'municipalities': data}, safe=False)


def get_barangays_by_municipality(request):
    """API endpoint to get barangays by municipality with optional search."""
    municipality_id = request.GET.get('municipality_id')
    search = request.GET.get('search', '').strip()
    
    if not municipality_id:
        return JsonResponse({'barangays': []}, safe=False)
    
    try:
        municipality = Municipality.objects.get(id=municipality_id)
        barangays = Barangay.objects.filter(municipality=municipality, is_active=True)
        if search:
            barangays = barangays.filter(name__icontains=search)
        barangays = barangays.order_by('name')[:100]
        data = [{'id': b.id, 'name': b.name} for b in barangays]
        return JsonResponse({'barangays': data}, safe=False)
    except Exception:
        return JsonResponse({'barangays': []}, safe=False)


def coordinator_delete(request, pk):
    """Delete a coordinator."""
    if request.method == 'POST' and not user_can_delete_in_operations(request.user):
        messages.error(request, 'You do not have permission to delete in Operations.')
        return redirect(f"{reverse('operations:coordinator')}?no_delete_perm=ops")
    obj = get_object_or_404(Coordinator, pk=pk)
    if request.method == 'POST':
        name = obj.fullname
        obj.delete()
        log_activity(request, ACTION_DELETE, f'Deleted coordinator "{name}".')
        messages.success(request, f'Coordinator "{name}" deleted.')
        return redirect('operations:coordinator')
    messages.error(request, 'Invalid request.')
    return redirect('operations:coordinator')


@transaction.atomic
def coordinator_position_add(request):
    """Add a coordinator position (for coordinator module only, not reference Position)."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if not name:
            messages.error(request, 'Position name is required.')
            return redirect('operations:coordinator')
        existing_codes = CoordinatorPosition.objects.exclude(code='').values_list('code', flat=True)
        numeric_codes = [int(c) for c in existing_codes if c.isdigit()]
        next_code = max(numeric_codes) + 1 if numeric_codes else 1
        CoordinatorPosition.objects.create(
            name=name,
            code=str(next_code),
            description=description,
            is_active=True,
        )
        log_activity(request, ACTION_CREATE, f'Added coordinator position "{name}" (code {next_code}).')
        messages.success(request, f'Coordinator position "{name}" added with code {next_code}.')
    return redirect('operations:coordinator')


def coordinator_position_edit(request, pk):
    """Edit a coordinator position."""
    obj = get_object_or_404(CoordinatorPosition, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Position name is required.')
            return redirect('operations:coordinator')
        code = request.POST.get('code', '').strip()
        obj.name = name
        obj.code = code
        obj.description = request.POST.get('description', '').strip()
        obj.is_active = request.POST.get('is_active') == 'on'
        obj.save()
        log_activity(request, ACTION_UPDATE, f'Updated coordinator position "{name}".')
        messages.success(request, f'Position "{name}" updated.')
    return redirect('operations:coordinator')


def coordinator_position_delete(request, pk):
    """Delete a coordinator position (only if no coordinators use it)."""
    if request.method == 'POST' and not user_can_delete_in_operations(request.user):
        messages.error(request, 'You do not have permission to delete in Operations.')
        return redirect(f"{reverse('operations:coordinator')}?no_delete_perm=ops")
    obj = get_object_or_404(CoordinatorPosition, pk=pk)
    if request.method == 'POST':
        if obj.coordinators.exists():
            messages.error(request, f'Cannot delete "{obj.name}": it is assigned to coordinator(s).')
        else:
            name = obj.name
            obj.delete()
            log_activity(request, ACTION_DELETE, f'Deleted coordinator position "{name}".')
            messages.success(request, f'Position "{name}" deleted.')
    return redirect('operations:coordinator')


def barangay_officials(request):
    """Display list of barangay officials."""
    officials = BarangayOfficial.objects.select_related('resident', 'barangay', 'barangay__municipality', 'position').filter(is_active=True)
    residents = Resident.objects.filter(status='ALIVE').order_by('lastname', 'firstname')
    barangays = Barangay.objects.filter(is_active=True).select_related('municipality')
    positions = Position.objects.filter(is_active=True)
    municipalities = Municipality.objects.filter(is_active=True).order_by('name')
    
    context = {
        'officials': officials,
        'residents': residents,
        'barangays': barangays,
        'positions': positions,
        'municipalities': municipalities,
    }
    return render(request, "operations/barangay_officials.html", context)


def residents_record(request):
    """Display list of residents."""
    residents = Resident.objects.select_related('barangay').all()
    barangays = Barangay.objects.filter(is_active=True)
    base_url = _get_base_url_for_devices(request)
    context = {
        'residents': residents,
        'barangays': barangays,
        'network_url': base_url,
    }
    return render(request, "operations/residents_record.html", context)


@transaction.atomic
def resident_add(request):
    """Add a new resident - synced to Supabase database."""
    if request.method == 'POST':
        try:
            # Get barangay
            barangay_id = request.POST.get('barangay')
            barangay = get_object_or_404(Barangay, id=barangay_id)
            
            # Create resident (automatically saved to Supabase)
            resident = Resident(
                barangay=barangay,
                status=request.POST.get('status', 'ALIVE'),
                profile_picture=request.FILES.get('profile_picture'),
                lastname=request.POST.get('lastname'),
                firstname=request.POST.get('firstname'),
                middlename=request.POST.get('middlename', ''),
                suffix=request.POST.get('suffix', ''),
                gender=request.POST.get('gender'),
                date_of_birth=request.POST.get('date_of_birth'),
                place_of_birth=request.POST.get('place_of_birth'),
                address=request.POST.get('address'),
                purok=request.POST.get('purok'),
                contact_no=request.POST.get('contact_no'),
                civil_status=request.POST.get('civil_status'),
                educational_attainment=request.POST.get('educational_attainment'),
                citizenship=request.POST.get('citizenship'),
                dialect_ethnic=request.POST.get('dialect_ethnic'),
                occupation=request.POST.get('occupation'),
                health_status=request.POST.get('health_status'),
                economic_status=request.POST.get('economic_status'),
                is_voter=request.POST.get('is_voter') == 'on',
                remarks=request.POST.get('remarks', ''),
            )
            resident.save()
            
            # Log successful save to Supabase
            logger.info(f'Resident {resident.get_full_name()} (ID: {resident.resident_id}) added to Supabase database successfully')
            
            log_activity(request, ACTION_CREATE, f'Added resident "{resident.get_full_name()}" ({barangay.name}).')
            messages.success(request, f'Resident {resident.get_full_name()} added successfully!')
            return redirect('operations:residents_record')
        except Exception as e:
            logger.error(f'Error adding resident to Supabase: {str(e)}')
            messages.error(request, f'Error adding resident: {str(e)}')
            return redirect('operations:residents_record')
    
    return redirect('operations:residents_record')


def resident_qr(request, pk):
    """Generate QR code image for resident profile (scannable URL to app)."""
    import qrcode
    import io
    resident = get_object_or_404(Resident, pk=pk)
    base = _get_base_url_for_devices(request)
    profile_url = f"{base}/app/resident/{pk}/"
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(profile_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#1a1d24', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type='image/png')


def resident_print(request, pk):
    """Render print template for resident (record layout: name, details, address, QR, profile)."""
    resident = get_object_or_404(Resident, pk=pk)
    profile_picture_url = ''
    if resident.profile_picture:
        try:
            profile_picture_url = request.build_absolute_uri(resident.profile_picture.url)
        except Exception:
            profile_picture_url = ''
    # Format: LASTNAME, FIRSTNAME SUFFIX MIDDLENAME
    parts = [resident.lastname or '']
    name_parts = [resident.firstname or '', resident.suffix or '', resident.middlename or '']
    parts.append(' '.join(p for p in name_parts if p).strip())
    full_name = ', '.join(p for p in parts if p).upper() or '-'
    birthdate = resident.date_of_birth.strftime('%b-%d-%Y') if resident.date_of_birth else '-'
    age = str(resident.get_age()) if resident.date_of_birth else '-'
    address_line = f"{resident.address or ''}{', ' + resident.purok if resident.purok else ''}".strip() or '-'
    qr_code_url = request.build_absolute_uri(reverse('operations:resident_qr', args=[pk]))
    # Badges per Profiling-template.docx: PWD, SENIOR (VOTERS shown under QR)
    badges = []
    if resident.health_status == 'PWD':
        badges.append('PWD')
    if resident.economic_status == 'SENIOR CITIZEN':
        badges.append('SENIOR')
    barangay_name = resident.barangay.name if resident.barangay else ''
    resident_id_val = resident.resident_id or str(resident.id)
    id_barangay = f"{resident_id_val}. {barangay_name}" if barangay_name else resident_id_val
    return render(request, 'operations/resident_print.html', {
        'resident': resident,
        'profile_picture_url': profile_picture_url,
        'full_name': full_name,
        'birthdate': birthdate,
        'age': age,
        'address_line': address_line,
        'qr_code_url': qr_code_url,
        'badges': badges,
        'barangay_name': barangay_name,
        'id_barangay': id_barangay,
    })


def resident_get(request, pk):
    """Get resident data as JSON."""
    resident = get_object_or_404(Resident, pk=pk)
    profile_url = ''
    if resident.profile_picture:
        try:
            profile_url = request.build_absolute_uri(resident.profile_picture.url)
        except Exception:
            profile_url = ''
    barangay_id = resident.barangay.id if resident.barangay else None
    barangay_name = resident.barangay.name if resident.barangay else ''
    date_of_birth_str = ''
    if resident.date_of_birth:
        date_of_birth_str = resident.date_of_birth.strftime('%Y-%m-%d')
    date_verified_str = ''
    if resident.date_verified:
        try:
            date_verified_str = resident.date_verified.strftime('%Y-%m-%d')
        except Exception:
            date_verified_str = ''
    data = {
        'id': resident.id,
        'resident_id': resident.resident_id or '',
        'profile_picture': profile_url,
        'barangay': barangay_id,
        'barangay_name': barangay_name,
        'status': resident.status or 'ALIVE',
        'lastname': resident.lastname or '',
        'firstname': resident.firstname or '',
        'middlename': resident.middlename or '',
        'suffix': resident.suffix or '',
        'gender': resident.gender or '',
        'date_of_birth': date_of_birth_str,
        'place_of_birth': resident.place_of_birth or '',
        'address': resident.address or '',
        'purok': resident.purok or '',
        'contact_no': resident.contact_no or '',
        'civil_status': resident.civil_status or '',
        'educational_attainment': resident.educational_attainment or '',
        'citizenship': resident.citizenship or '',
        'dialect_ethnic': resident.dialect_ethnic or '',
        'occupation': resident.occupation or '',
        'health_status': resident.health_status or '',
        'economic_status': resident.economic_status or '',
        'is_voter': resident.is_voter,
        'precinct_number': resident.precinct_number or '',
        'voter_legend': resident.voter_legend or '',
        'date_verified': date_verified_str,
        'verified_by': resident.verified_by or '',
        'remarks': resident.remarks or '',
    }
    data['full_name'] = resident.get_full_name()
    base = _get_base_url_for_devices(request)
    data['profile_url'] = f"{base}/app/resident/{resident.pk}/"
    return JsonResponse(data)


@transaction.atomic
def resident_edit(request, pk):
    """Edit an existing resident - changes synced to Supabase database."""
    resident = get_object_or_404(Resident, pk=pk)
    
    if request.method == 'POST':
        try:
            # Store old name for logging
            old_name = resident.get_full_name()
            
            # Update fields (automatically saved to Supabase)
            barangay_id = request.POST.get('barangay')
            resident.barangay = get_object_or_404(Barangay, id=barangay_id)
            resident.status = request.POST.get('status', 'ALIVE')
            if 'profile_picture' in request.FILES:
                resident.profile_picture = request.FILES['profile_picture']
            resident.lastname = request.POST.get('lastname')
            resident.firstname = request.POST.get('firstname')
            resident.middlename = request.POST.get('middlename', '')
            resident.suffix = request.POST.get('suffix', '')
            resident.gender = request.POST.get('gender')
            resident.date_of_birth = request.POST.get('date_of_birth')
            resident.place_of_birth = request.POST.get('place_of_birth')
            resident.address = request.POST.get('address')
            resident.purok = request.POST.get('purok')
            resident.contact_no = request.POST.get('contact_no')
            resident.civil_status = request.POST.get('civil_status')
            resident.educational_attainment = request.POST.get('educational_attainment')
            resident.citizenship = request.POST.get('citizenship')
            resident.dialect_ethnic = request.POST.get('dialect_ethnic')
            resident.occupation = request.POST.get('occupation')
            resident.health_status = request.POST.get('health_status')
            resident.economic_status = request.POST.get('economic_status')
            resident.is_voter = request.POST.get('is_voter') == 'on'
            resident.precinct_number = request.POST.get('precinct_number', '').strip()
            # Legend: comma-separated e.g. A,B or A,B,C (Illiterate, PWD, Senior)
            resident.voter_legend = request.POST.get('voter_legend', '').strip()
            date_verified_val = request.POST.get('date_verified', '').strip()
            resident.date_verified = None
            if date_verified_val:
                try:
                    from datetime import datetime
                    resident.date_verified = datetime.strptime(date_verified_val, '%Y-%m-%d').date()
                except ValueError:
                    pass
            # Verified by: set to the logged-in user's full name (or username if no full name)
            resident.verified_by = (request.user.get_full_name() or request.user.get_username() or '').strip()
            resident.remarks = request.POST.get('remarks', '')
            
            resident.save()
            
            # Log successful update to Supabase
            logger.info(f'Resident {old_name} (ID: {resident.resident_id}) updated to {resident.get_full_name()} in Supabase database')
            
            log_activity(request, ACTION_UPDATE, f'Updated resident "{resident.get_full_name()}".')
            messages.success(request, f'Resident {resident.get_full_name()} updated successfully!')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Voter updated successfully.'})
            return redirect('operations:residents_record')
        except Exception as e:
            logger.error(f'Error updating resident in Supabase: {str(e)}')
            messages.error(request, f'Error updating resident: {str(e)}')
            return redirect('operations:residents_record')
    
    return redirect('operations:residents_record')


@transaction.atomic
def resident_delete(request, pk):
    """Delete a resident - removed from Supabase database."""
    if request.method == 'POST' and not user_can_delete_in_operations(request.user):
        messages.error(request, 'You do not have permission to delete in Operations.')
        return redirect(f"{reverse('operations:residents_record')}?no_delete_perm=ops")
    resident = get_object_or_404(Resident, pk=pk)
    
    if request.method == 'POST':
        try:
            name = resident.get_full_name()
            resident_id = resident.resident_id
            
            # Delete from database (automatically removes from Supabase)
            resident.delete()
            
            # Log successful deletion from Supabase
            logger.info(f'Resident {name} (ID: {resident_id}) deleted from Supabase database')
            
            log_activity(request, ACTION_DELETE, f'Deleted resident "{name}".')
            messages.success(request, f'Resident {name} deleted successfully!')
        except Exception as e:
            logger.error(f'Error deleting resident from Supabase: {str(e)}')
            messages.error(request, f'Error deleting resident: {str(e)}')
    
    return redirect('operations:residents_record')


def voters_registration(request):
    """Voters registration: show municipalities, then barangays; clicking a barangay shows its voters."""
    barangays_with_voter_count = Barangay.objects.filter(
        is_active=True
    ).annotate(
        voter_count=Count(
            'residents',
            filter=Q(residents__is_voter=True, residents__status=Resident.STATUS_ALIVE),
            distinct=True,
        ),
    ).order_by('name')
    municipalities = Municipality.objects.filter(
        is_active=True
    ).prefetch_related(
        Prefetch('barangays', queryset=barangays_with_voter_count)
    ).order_by('name')
    context = {'municipalities': municipalities}
    return render(request, "operations/voters_registration.html", context)


def voters_registration_barangay(request, pk):
    """Voters registration detail page for a single barangay (full-width voters list)."""
    barangays_with_voter_count = Barangay.objects.filter(
        is_active=True
    ).annotate(
        voter_count=Count(
            'residents',
            filter=Q(residents__is_voter=True, residents__status=Resident.STATUS_ALIVE),
            distinct=True,
        ),
    ).order_by('name')
    municipalities = Municipality.objects.filter(
        is_active=True
    ).prefetch_related(
        Prefetch('barangays', queryset=barangays_with_voter_count)
    ).order_by('name')
    initial_barangay = get_object_or_404(Barangay, pk=pk, is_active=True)
    context = {
        'municipalities': municipalities,
        'initial_barangay': initial_barangay,
        'single_barangay_view': True,
    }
    return render(request, "operations/voters_registration.html", context)


def get_voters_by_barangay(request, pk):
    """API: return list of voters (residents with is_voter=True, alive) for a barangay."""
    barangay = get_object_or_404(Barangay, pk=pk)
    voters = Resident.objects.filter(
        barangay=barangay,
        is_voter=True,
        status=Resident.STATUS_ALIVE,
    ).order_by('lastname', 'firstname')
    barangay_name = barangay.name
    data = [
        {
            'id': r.id,
            'resident_id': r.resident_id or '',
            'full_name': r.get_full_name(),
            'gender': r.get_gender_display() if hasattr(r, 'get_gender_display') else r.gender,
            'date_of_birth': r.date_of_birth.strftime('%Y-%m-%d'),
            'address': r.address or '',
            'purok': r.purok or '',
            'precinct_number': r.precinct_number or '—',
            'barangay_name': barangay_name,
            'legend': r.get_voter_legend_display(),
            'status': r.get_status_display() if hasattr(r, 'get_status_display') else r.status,
            'date_verified': r.date_verified.strftime('%Y-%m-%d') if r.date_verified else '',
            'verified_by': r.verified_by or '',
        }
        for r in voters
    ]
    return JsonResponse({'voters': data, 'barangay_name': barangay_name}, safe=False)


@transaction.atomic
def barangay_official_add(request):
    """Add a new barangay official."""
    if request.method == 'POST':
        try:
            resident_id = request.POST.get('resident')
            barangay_id = request.POST.get('barangay')
            position_id = request.POST.get('position')
            
            resident = get_object_or_404(Resident, id=resident_id)
            barangay = get_object_or_404(Barangay, id=barangay_id)
            position = get_object_or_404(Position, id=position_id)
            
            if BarangayOfficial.objects.filter(resident=resident, barangay=barangay, is_active=True).exists():
                messages.error(
                    request,
                    f'{resident.get_full_name()} is already registered as an official in {barangay.name}. '
                    'The same person cannot be added twice in the same barangay.'
                )
                return redirect('operations:barangay_officials')
            
            official = BarangayOfficial(
                resident=resident,
                barangay=barangay,
                position=position,
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date') or None,
                remarks=request.POST.get('remarks', ''),
            )
            official.save()
            
            log_activity(request, ACTION_CREATE, f'Added barangay official "{resident.get_full_name()}" as {position.name} in {barangay.name}.')
            logger.info(f'Barangay official {resident.get_full_name()} added as {position.name} in {barangay.name}')
            
            messages.success(request, f'{resident.get_full_name()} added as {position.name} successfully!')
            return redirect('operations:barangay_officials')
        except Exception as e:
            logger.error(f'Error adding barangay official: {str(e)}')
            messages.error(request, f'Error adding official: {str(e)}')
            return redirect('operations:barangay_officials')
    
    return redirect('operations:barangay_officials')


def barangay_official_get(request, pk):
    """Get barangay official data as JSON."""
    official = get_object_or_404(
        BarangayOfficial.objects.select_related('barangay', 'barangay__municipality'),
        pk=pk
    )
    barangay = official.barangay
    data = {
        'id': official.id,
        'resident': official.resident.id,
        'barangay': barangay.id,
        'municipality': barangay.municipality_id if barangay.municipality_id else '',
        'municipality_name': barangay.municipality.name if barangay.municipality else '',
        'position': official.position.id,
        'resident_name': official.resident.get_full_name(),
        'barangay_name': barangay.name,
        'position_name': official.position.name,
        'start_date': official.start_date.strftime('%Y-%m-%d'),
        'end_date': official.end_date.strftime('%Y-%m-%d') if official.end_date else '',
        'remarks': official.remarks or '',
    }
    return JsonResponse(data)


@transaction.atomic
def barangay_official_edit(request, pk):
    """Edit an existing barangay official."""
    official = get_object_or_404(BarangayOfficial, pk=pk)
    
    if request.method == 'POST':
        try:
            resident_id = request.POST.get('resident')
            barangay_id = request.POST.get('barangay')
            position_id = request.POST.get('position')
            
            resident = get_object_or_404(Resident, id=resident_id)
            barangay = get_object_or_404(Barangay, id=barangay_id)
            position = get_object_or_404(Position, id=position_id)
            
            existing = BarangayOfficial.objects.filter(
                resident=resident, barangay=barangay, is_active=True
            ).exclude(pk=pk)
            if existing.exists():
                messages.error(
                    request,
                    f'{resident.get_full_name()} is already registered as an official in {barangay.name}. '
                    'The same person cannot be listed twice in the same barangay.'
                )
                return redirect('operations:barangay_officials')
            
            official.resident = resident
            official.barangay = barangay
            official.position = position
            official.start_date = request.POST.get('start_date')
            official.end_date = request.POST.get('end_date') or None
            official.remarks = request.POST.get('remarks', '')
            
            official.save()
            
            log_activity(request, ACTION_UPDATE, f'Updated barangay official "{official.resident.get_full_name()}" ({barangay.name}).')
            logger.info(f'Barangay official {official.resident.get_full_name()} updated')
            
            messages.success(request, f'{official.resident.get_full_name()} updated successfully!')
            return redirect('operations:barangay_officials')
        except Exception as e:
            logger.error(f'Error updating barangay official: {str(e)}')
            messages.error(request, f'Error updating official: {str(e)}')
            return redirect('operations:barangay_officials')
    
    return redirect('operations:barangay_officials')


@transaction.atomic
def barangay_official_delete(request, pk):
    """Delete a barangay official."""
    if request.method == 'POST' and not user_can_delete_in_operations(request.user):
        messages.error(request, 'You do not have permission to delete in Operations.')
        return redirect(f"{reverse('operations:barangay_officials')}?no_delete_perm=ops")
    official = get_object_or_404(BarangayOfficial, pk=pk)
    
    if request.method == 'POST':
        try:
            name = official.resident.get_full_name()
            position = official.position.name
            
            official.delete()
            
            log_activity(request, ACTION_DELETE, f'Deleted barangay official "{name}" ({position}).')
            logger.info(f'Barangay official {name} ({position}) deleted')
            
            messages.success(request, f'{name} removed from {position} successfully!')
        except Exception as e:
            logger.error(f'Error deleting barangay official: {str(e)}')
            messages.error(request, f'Error deleting official: {str(e)}')
    
    return redirect('operations:barangay_officials')
