from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from reference.models import Barangay
from .models import Resident
import logging

# Set up logging
logger = logging.getLogger(__name__)


def operations_index(request):
    return render(request, "operations/operations_index.html")


def coordinator(request):
    return render(request, "operations/coordinator.html")


def barangay_officials(request):
    return render(request, "operations/barangay_officials.html")


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
            
            messages.success(request, f'Resident {resident.get_full_name()} added successfully and synced to Supabase!')
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
            
            messages.success(request, f'Resident {resident.get_full_name()} updated successfully and synced to Supabase!')
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
            
            messages.success(request, f'Resident {name} deleted successfully from Supabase!')
        except Exception as e:
            logger.error(f'Error deleting resident from Supabase: {str(e)}')
            messages.error(request, f'Error deleting resident: {str(e)}')
    
    return redirect('operations:residents_record')


def voters_registration(request):
    return render(request, "operations/voters_registration.html")
