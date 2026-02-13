from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from .models import Barangay, Position


def reference_index(request):
    """Reference landing page with links to Barangay and Positions."""
    return render(request, 'reference/reference_index.html')


def barangay_list(request):
    """List all active barangays ordered by code."""
    barangays = Barangay.objects.filter(is_active=True).order_by('code')
    return render(request, 'reference/barangay_list.html', {'barangays': barangays})


@transaction.atomic
def barangay_add(request):
    """Add a new barangay."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, 'Barangay name is required.')
            return redirect('reference:barangay_list')
        
        # Auto-generate code: find first available number (fill gaps)
        # Get all existing codes from active barangays only
        existing_codes = Barangay.objects.filter(is_active=True).exclude(code='').values_list('code', flat=True)
        numeric_codes = sorted([int(c) for c in existing_codes if c.isdigit()])
        
        # Find the first missing number in the sequence
        next_code = 1
        for code in numeric_codes:
            if code == next_code:
                next_code += 1
            else:
                break
        
        # Create and save the barangay
        barangay = Barangay.objects.create(
            name=name,
            code=str(next_code),
            description=description,
            is_active=True
        )
        # Force commit to database
        transaction.on_commit(lambda: None)
        
        messages.success(request, f'Barangay "{name}" has been added successfully with code {next_code}.')
        return redirect('reference:barangay_list')
    
    return redirect('reference:barangay_list')


@transaction.atomic
def barangay_edit(request, pk):
    """Edit an existing barangay."""
    barangay = get_object_or_404(Barangay, pk=pk, is_active=True)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, 'Barangay name is required.')
            return redirect('reference:barangay_list')
        
        # Update barangay data
        barangay.name = name
        barangay.description = description
        # Code is not updated - it remains the same
        barangay.save(update_fields=['name', 'description', 'updated_at'])
        # Force commit to database
        transaction.on_commit(lambda: None)
        
        messages.success(request, f'Barangay "{name}" has been updated successfully.')
        return redirect('reference:barangay_list')
    
    return redirect('reference:barangay_list')


@transaction.atomic
def barangay_delete(request, pk):
    """Delete a barangay (soft delete by setting is_active to False)."""
    barangay = get_object_or_404(Barangay, pk=pk, is_active=True)
    
    if request.method == 'POST':
        barangay_name = barangay.name
        barangay_code = barangay.code
        # Soft delete: set is_active to False (keeps data in database)
        barangay.is_active = False
        barangay.save(update_fields=['is_active', 'updated_at'])
        # Force commit to database
        transaction.on_commit(lambda: None)
        
        messages.success(request, f'Barangay "{barangay_name}" (Code: {barangay_code}) has been deleted successfully.')
        return redirect('reference:barangay_list')
    
    return redirect('reference:barangay_list')


def barangay_get(request, pk):
    """Get barangay details as JSON for editing."""
    barangay = get_object_or_404(Barangay, pk=pk, is_active=True)
    data = {
        'id': barangay.id,
        'name': barangay.name,
        'code': barangay.code,
        'description': barangay.description,
    }
    return JsonResponse(data)


def position_list(request):
    """List all active positions."""
    positions = Position.objects.filter(is_active=True)
    return render(request, 'reference/position_list.html', {'positions': positions})
