from django.core.management.base import BaseCommand
from reference.models import Barangay


class Command(BaseCommand):
    help = 'Re-sequence barangay codes to be sequential starting from 1'

    def handle(self, *args, **options):
        # Get all barangays ordered by their current code (numeric)
        barangays = Barangay.objects.all()
        
        # Convert codes to integers for proper sorting
        barangay_list = []
        for brgy in barangays:
            if brgy.code.isdigit():
                barangay_list.append((int(brgy.code), brgy))
            else:
                barangay_list.append((0, brgy))
        
        # Sort by code
        barangay_list.sort(key=lambda x: x[0])
        
        # Re-assign codes sequentially starting from 1
        self.stdout.write(self.style.WARNING('Starting re-sequencing...'))
        
        for index, (old_code, barangay) in enumerate(barangay_list, start=1):
            old_code_str = barangay.code
            new_code_str = str(index)
            
            if old_code_str != new_code_str:
                barangay.code = new_code_str
                barangay.save(update_fields=['code', 'updated_at'])
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated: {barangay.name} - Code {old_code_str} → {new_code_str}'
                    )
                )
            else:
                self.stdout.write(
                    f'Unchanged: {barangay.name} - Code {old_code_str}'
                )
        
        self.stdout.write(self.style.SUCCESS('\nRe-sequencing completed successfully!'))
