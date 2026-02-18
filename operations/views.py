from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q
from reference.models import Barangay, Position
from .models import Resident, BarangayOfficial, CoordinatorPosition, Coordinator
import logging

# Set up logging
logger = logging.getLogger(__name__)


def operations_index(request):
    return render(request, "operations/operations_index.html")


def coordinator(request):
    """Coordinator page; positions are coordinator-only (CoordinatorPosition), not reference Position."""
    coordinator_positions = CoordinatorPosition.objects.filter(is_active=True).order_by('code')
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
        'coordinators': coordinators,
        'barangays': barangays,
        'search_query': search_query,
    }
    return render(request, "operations/coordinator.html", context)


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
        position = get_object_or_404(CoordinatorPosition, id=position_id)
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
            contact_no=request.POST.get('contact_no', ''),
            remarks=request.POST.get('remarks', ''),
            date_start=date_start,
            is_active=request.POST.get('is_active') == 'on',
        )
        messages.success(request, f'Coordinator "{fullname}" added successfully.')
    return redirect('operations:coordinator')


def coordinator_edit(request, pk):
    """Edit an existing coordinator."""
    obj = get_object_or_404(Coordinator, pk=pk)
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
        position = get_object_or_404(CoordinatorPosition, id=position_id)
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
        obj.contact_no = request.POST.get('contact_no', '')
        obj.remarks = request.POST.get('remarks', '')
        obj.date_start = date_start
        obj.is_active = request.POST.get('is_active') == 'on'
        obj.save()
        messages.success(request, f'Coordinator "{fullname}" updated successfully.')
        return redirect('operations:coordinator')
    context = {
        'coordinator': obj,
        'barangays': barangays,
        'coordinator_positions': coordinator_positions,
    }
    return render(request, "operations/coordinator_edit.html", context)


def coordinator_delete(request, pk):
    """Delete a coordinator."""
    obj = get_object_or_404(Coordinator, pk=pk)
    if request.method == 'POST':
        name = obj.fullname
        obj.delete()
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
        messages.success(request, f'Coordinator position "{name}" added with code {next_code}.')
    return redirect('operations:coordinator')


def barangay_officials(request):
    """Display list of barangay officials."""
    officials = BarangayOfficial.objects.select_related('resident', 'barangay', 'position').filter(is_active=True)
    residents = Resident.objects.filter(status='ALIVE').order_by('lastname', 'firstname')
    barangays = Barangay.objects.filter(is_active=True)
    positions = Position.objects.filter(is_active=True)
    
    context = {
        'officials': officials,
        'residents': residents,
        'barangays': barangays,
        'positions': positions,
    }
    return render(request, "operations/barangay_officials.html", context)


def residents_record(request):
    """Display list of residents."""
    residents = Resident.objects.select_related('barangay').all()
    barangays = Barangay.objects.filter(is_active=True)
    
    context = {
        'residents': residents,
        'barangays': barangays,
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
            
            messages.success(request, f'Resident {resident.get_full_name()} added successfully!')
            return redirect('operations:residents_record')
        except Exception as e:
            logger.error(f'Error adding resident to Supabase: {str(e)}')
            messages.error(request, f'Error adding resident: {str(e)}')
            return redirect('operations:residents_record')
    
    return redirect('operations:residents_record')


def resident_get(request, pk):
    """Get resident data as JSON."""
    resident = get_object_or_404(Resident, pk=pk)
    data = {
        'id': resident.id,
        'resident_id': resident.resident_id,
        'barangay': resident.barangay.id,
        'status': resident.status,
        'lastname': resident.lastname,
        'firstname': resident.firstname,
        'middlename': resident.middlename,
        'suffix': resident.suffix,
        'gender': resident.gender,
        'date_of_birth': resident.date_of_birth.strftime('%Y-%m-%d'),
        'place_of_birth': resident.place_of_birth,
        'address': resident.address,
        'purok': resident.purok,
        'contact_no': resident.contact_no,
        'civil_status': resident.civil_status,
        'educational_attainment': resident.educational_attainment,
        'citizenship': resident.citizenship,
        'dialect_ethnic': resident.dialect_ethnic,
        'occupation': resident.occupation,
        'health_status': resident.health_status,
        'economic_status': resident.economic_status,
        'is_voter': resident.is_voter,
        'remarks': resident.remarks,
    }
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
            resident.remarks = request.POST.get('remarks', '')
            
            resident.save()
            
            # Log successful update to Supabase
            logger.info(f'Resident {old_name} (ID: {resident.resident_id}) updated to {resident.get_full_name()} in Supabase database')
            
            messages.success(request, f'Resident {resident.get_full_name()} updated successfully!')
            return redirect('operations:residents_record')
        except Exception as e:
            logger.error(f'Error updating resident in Supabase: {str(e)}')
            messages.error(request, f'Error updating resident: {str(e)}')
            return redirect('operations:residents_record')
    
    return redirect('operations:residents_record')


@transaction.atomic
def resident_delete(request, pk):
    """Delete a resident - removed from Supabase database."""
    resident = get_object_or_404(Resident, pk=pk)
    
    if request.method == 'POST':
        try:
            name = resident.get_full_name()
            resident_id = resident.resident_id
            
            # Delete from database (automatically removes from Supabase)
            resident.delete()
            
            # Log successful deletion from Supabase
            logger.info(f'Resident {name} (ID: {resident_id}) deleted from Supabase database')
            
            messages.success(request, f'Resident {name} deleted successfully!')
        except Exception as e:
            logger.error(f'Error deleting resident from Supabase: {str(e)}')
            messages.error(request, f'Error deleting resident: {str(e)}')
    
    return redirect('operations:residents_record')


def voters_registration(request):
    return render(request, "operations/voters_registration.html")


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
            
            official = BarangayOfficial(
                resident=resident,
                barangay=barangay,
                position=position,
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date') or None,
                remarks=request.POST.get('remarks', ''),
            )
            official.save()
            
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
    official = get_object_or_404(BarangayOfficial, pk=pk)
    data = {
        'id': official.id,
        'resident': official.resident.id,
        'barangay': official.barangay.id,
        'position': official.position.id,
        'start_date': official.start_date.strftime('%Y-%m-%d'),
        'end_date': official.end_date.strftime('%Y-%m-%d') if official.end_date else '',
        'remarks': official.remarks,
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
            
            official.resident = get_object_or_404(Resident, id=resident_id)
            official.barangay = get_object_or_404(Barangay, id=barangay_id)
            official.position = get_object_or_404(Position, id=position_id)
            official.start_date = request.POST.get('start_date')
            official.end_date = request.POST.get('end_date') or None
            official.remarks = request.POST.get('remarks', '')
            
            official.save()
            
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
    official = get_object_or_404(BarangayOfficial, pk=pk)
    
    if request.method == 'POST':
        try:
            name = official.resident.get_full_name()
            position = official.position.name
            
            official.delete()
            
            logger.info(f'Barangay official {name} ({position}) deleted')
            
            messages.success(request, f'{name} removed from {position} successfully!')
        except Exception as e:
            logger.error(f'Error deleting barangay official: {str(e)}')
            messages.error(request, f'Error deleting official: {str(e)}')
    
    return redirect('operations:barangay_officials')
