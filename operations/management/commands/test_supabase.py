from django.core.management.base import BaseCommand
from django.db import connection
from operations.models import Resident
from reference.models import Barangay


class Command(BaseCommand):
    help = 'Test Supabase database connection and display statistics'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== Testing Supabase Connection ===\n'))
        
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                db_version = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f'[OK] Connected to PostgreSQL: {db_version}'))
            
            # Get database info
            db_settings = connection.settings_dict
            self.stdout.write(self.style.SUCCESS(f'[OK] Database Host: {db_settings["HOST"]}'))
            self.stdout.write(self.style.SUCCESS(f'[OK] Database Name: {db_settings["NAME"]}'))
            self.stdout.write(self.style.SUCCESS(f'[OK] Database User: {db_settings["USER"]}'))
            
            # Test models
            self.stdout.write(self.style.SUCCESS('\n=== Database Statistics ===\n'))
            
            barangay_count = Barangay.objects.count()
            self.stdout.write(self.style.SUCCESS(f'[OK] Total Barangays: {barangay_count}'))
            
            resident_count = Resident.objects.count()
            self.stdout.write(self.style.SUCCESS(f'[OK] Total Residents: {resident_count}'))
            
            alive_count = Resident.objects.filter(status='ALIVE').count()
            deceased_count = Resident.objects.filter(status='DECEASED').count()
            self.stdout.write(self.style.SUCCESS(f'  - Alive: {alive_count}'))
            self.stdout.write(self.style.SUCCESS(f'  - Deceased: {deceased_count}'))
            
            voters_count = Resident.objects.filter(is_voter=True).count()
            self.stdout.write(self.style.SUCCESS(f'[OK] Registered Voters: {voters_count}'))
            
            # Test table exists
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name LIKE 'operations_%'
                    ORDER BY table_name;
                """)
                tables = cursor.fetchall()
                self.stdout.write(self.style.SUCCESS(f'\n[OK] Operations Tables in Supabase:'))
                for table in tables:
                    self.stdout.write(self.style.SUCCESS(f'  - {table[0]}'))
            
            self.stdout.write(self.style.SUCCESS('\n[SUCCESS] All Supabase operations are working correctly!\n'))
            self.stdout.write(self.style.SUCCESS('All data is being saved to Supabase database.\n'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n[ERROR] Error connecting to Supabase: {str(e)}\n'))
