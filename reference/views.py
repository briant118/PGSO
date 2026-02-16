from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from .models import Barangay, Position
from operations.models import BarangayOfficial


def reference_index(request):
    """Reference landing page with links to Barangay and Positions."""
    return render(request, 'reference/reference_index.html')


def barangay_list(request):
    """List all active barangays ordered by code."""
    barangays = Barangay.objects.filter(is_active=True)
    # Sort by numeric code value instead of alphabetically
    barangays = sorted(barangays, key=lambda x: int(x.code) if x.code.isdigit() else 999999)
    return render(request, 'reference/barangay_list.html', {'barangays': barangays})


@transaction.atomic
def barangay_add(request):
    """Add a new barangay."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        municipality = request.POST.get('municipality', '').strip()
        
        if not name:
            messages.error(request, 'Barangay name is required.')
            return redirect('reference:barangay_list')
        
        # Auto-increment code: get maximum code and add 1 (no gap filling)
        # Get all existing codes from all barangays (including inactive ones)
        existing_codes = Barangay.objects.exclude(code='').values_list('code', flat=True)
        numeric_codes = [int(c) for c in existing_codes if c.isdigit()]
        
        # Get the maximum code and increment by 1
        next_code = max(numeric_codes) + 1 if numeric_codes else 1
        
        # Create and save the barangay
        barangay = Barangay.objects.create(
            name=name,
            code=str(next_code),
            municipality=municipality,
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
        municipality = request.POST.get('municipality', '').strip()
        
        if not name:
            messages.error(request, 'Barangay name is required.')
            return redirect('reference:barangay_list')
        
        # Update barangay data
        barangay.name = name
        barangay.municipality = municipality
        # Code is not updated - it remains the same
        barangay.save(update_fields=['name', 'municipality', 'updated_at'])
        # Force commit to database
        transaction.on_commit(lambda: None)
        
        messages.success(request, f'Barangay "{name}" has been updated successfully.')
        return redirect('reference:barangay_list')
    
    return redirect('reference:barangay_list')


@transaction.atomic
def barangay_delete(request, pk):
    """Delete a barangay and re-sequence all codes."""
    barangay = get_object_or_404(Barangay, pk=pk, is_active=True)
    
    if request.method == 'POST':
        barangay_name = barangay.name
        barangay_code = int(barangay.code) if barangay.code.isdigit() else 0
        
        # Hard delete: permanently remove from database
        barangay.delete()
        
        # Re-sequence all barangays with codes greater than the deleted one
        if barangay_code > 0:
            # Get all barangays and re-sequence their codes
            all_barangays = Barangay.objects.all().order_by('id')
            
            for brgy in all_barangays:
                if brgy.code.isdigit():
                    current_code = int(brgy.code)
                    # If this barangay's code is greater than deleted code, decrement it
                    if current_code > barangay_code:
                        brgy.code = str(current_code - 1)
                        brgy.save(update_fields=['code', 'updated_at'])
        
        # Force commit to database
        transaction.on_commit(lambda: None)
        
        messages.success(request, f'Barangay "{barangay_name}" (Code: {barangay_code}) has been deleted and codes have been re-sequenced.')
        return redirect('reference:barangay_list')
    
    return redirect('reference:barangay_list')


def barangay_get(request, pk):
    """Get barangay details as JSON for editing."""
    barangay = get_object_or_404(Barangay, pk=pk, is_active=True)
    data = {
        'id': barangay.id,
        'name': barangay.name,
        'code': barangay.code,
        'municipality': barangay.municipality,
    }
    return JsonResponse(data)


def position_list(request):
    """List all active positions ordered by code."""
    positions = Position.objects.filter(is_active=True)
    # Sort by numeric code value instead of alphabetically
    positions = sorted(positions, key=lambda x: int(x.code) if x.code.isdigit() else 999999)
    
    # Add total count for each position from BarangayOfficial model
    for position in positions:
        position.total = BarangayOfficial.objects.filter(position=position, is_active=True).count()
    
    return render(request, 'reference/position_list.html', {'positions': positions})


@transaction.atomic
def position_add(request):
    """Add a new position."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, 'Position name is required.')
            return redirect('reference:position_list')
        
        # Auto-increment code: get maximum code and add 1 (no gap filling)
        # Get all existing codes from all positions (including inactive ones)
        existing_codes = Position.objects.exclude(code='').values_list('code', flat=True)
        numeric_codes = [int(c) for c in existing_codes if c.isdigit()]
        
        # Get the maximum code and increment by 1
        next_code = max(numeric_codes) + 1 if numeric_codes else 1
        
        # Create and save the position
        position = Position.objects.create(
            name=name,
            code=str(next_code),
            description=description,
            is_active=True
        )
        # Force commit to database
        transaction.on_commit(lambda: None)
        
        messages.success(request, f'Position "{name}" has been added successfully with code {next_code}.')
        return redirect('reference:position_list')
    
    return redirect('reference:position_list')


@transaction.atomic
def position_edit(request, pk):
    """Edit an existing position."""
    position = get_object_or_404(Position, pk=pk, is_active=True)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, 'Position name is required.')
            return redirect('reference:position_list')
        
        # Update position data
        position.name = name
        position.description = description
        # Code is not updated - it remains the same
        position.save(update_fields=['name', 'description', 'updated_at'])
        # Force commit to database
        transaction.on_commit(lambda: None)
        
        messages.success(request, f'Position "{name}" has been updated successfully.')
        return redirect('reference:position_list')
    
    return redirect('reference:position_list')


@transaction.atomic
def position_delete(request, pk):
    """Delete a position and re-sequence all codes."""
    position = get_object_or_404(Position, pk=pk, is_active=True)
    
    if request.method == 'POST':
        position_name = position.name
        position_code = int(position.code) if position.code.isdigit() else 0
        
        # Hard delete: permanently remove from database
        position.delete()
        
        # Re-sequence all positions with codes greater than the deleted one
        if position_code > 0:
            # Get all positions and re-sequence their codes
            all_positions = Position.objects.all().order_by('id')
            
            for pos in all_positions:
                if pos.code.isdigit():
                    current_code = int(pos.code)
                    # If this position's code is greater than deleted code, decrement it
                    if current_code > position_code:
                        pos.code = str(current_code - 1)
                        pos.save(update_fields=['code', 'updated_at'])
        
        # Force commit to database
        transaction.on_commit(lambda: None)
        
        messages.success(request, f'Position "{position_name}" (Code: {position_code}) has been deleted and codes have been re-sequenced.')
        return redirect('reference:position_list')
    
    return redirect('reference:position_list')


def position_get(request, pk):
    """Get position details as JSON for editing."""
    position = get_object_or_404(Position, pk=pk, is_active=True)
    data = {
        'id': position.id,
        'name': position.name,
        'code': position.code,
        'description': position.description,
    }
    return JsonResponse(data)


def position_detail(request, pk):
    """Show list of barangays for a specific position."""
    position = get_object_or_404(Position, pk=pk)
    
    # Get municipality filter from request
    selected_municipality = request.GET.get('municipality', '')
    
    # Get unique municipalities from barangays
    municipalities = Barangay.objects.filter(
        is_active=True,
        municipality__isnull=False
    ).exclude(municipality='').values_list('municipality', flat=True).distinct().order_by('municipality')
    
    # Convert to list of dictionaries for template
    municipalities_list = [{'name': m} for m in municipalities]
    
    # Get barangays - all if no filter, filtered by municipality if filter is selected
    if selected_municipality:
        barangays = Barangay.objects.filter(
            is_active=True,
            municipality=selected_municipality
        ).order_by('name')
    else:
        # Show all barangays when no municipality filter is selected
        barangays = Barangay.objects.filter(is_active=True).order_by('name')
    
    # Add official count for each barangay for this position
    for barangay in barangays:
        barangay.officials_count = BarangayOfficial.objects.filter(
            position=position,
            barangay=barangay,
            is_active=True
        ).count()
    
    context = {
        'position': position,
        'municipalities': municipalities_list,
        'selected_municipality': selected_municipality,
        'barangays': barangays,
    }
    return render(request, 'reference/position_detail.html', context)


def position_barangay_officials(request, position_pk, barangay_pk):
    """Show list of officials for a specific position in a specific barangay."""
    position = get_object_or_404(Position, pk=position_pk)
    barangay = get_object_or_404(Barangay, pk=barangay_pk, is_active=True)
    
    # Get officials for this position and barangay from BarangayOfficial model
    barangay_officials = BarangayOfficial.objects.filter(
        position=position,
        barangay=barangay,
        is_active=True
    ).select_related('resident').order_by('resident__lastname', 'resident__firstname')
    
    # Format the data for the template
    officials = []
    for official in barangay_officials:
        officials.append({
            'name': official.resident.get_full_name(),
            'contact': official.resident.contact_no,
            'address': official.resident.address,
            'is_active': official.is_active,
        })
    
    context = {
        'position': position,
        'barangay': barangay,
        'officials': officials,
    }
    return render(request, 'reference/position_barangay_officials.html', context)
