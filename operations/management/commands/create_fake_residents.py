"""
Create around 200 fake residents with random gender, status, birth year, PWD, 4Ps, solo parent, senior.
Run: python manage.py create_fake_residents
"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from operations.models import Resident
from reference.models import Barangay


# Fake names (Filipino-style first and last names)
FIRST_NAMES_MALE = [
    'Juan', 'Pedro', 'Jose', 'Antonio', 'Manuel', 'Carlos', 'Miguel', 'Ramon', 'Fernando', 'Ricardo',
    'Eduardo', 'Alberto', 'Roberto', 'Francisco', 'Angel', 'Rafael', 'Luis', 'Enrique', 'Andres', 'Sergio',
    'Marco', 'Paolo', 'Christian', 'Mark', 'John', 'Michael', 'David', 'Daniel', 'James', 'Ryan',
]
FIRST_NAMES_FEMALE = [
    'Maria', 'Ana', 'Rosa', 'Carmen', 'Elena', 'Teresa', 'Rosa', 'Lourdes', 'Luz', 'Fe',
    'Grace', 'Joy', 'Mary', 'Elizabeth', 'Patricia', 'Jennifer', 'Michelle', 'Angela', 'Christine', 'Karen',
    'Anna', 'Maricar', 'Jasmine', 'Kristine', 'Catherine', 'Diana', 'Rose', 'Liza', 'Marilyn', 'Nina',
]
LAST_NAMES = [
    'Dela Cruz', 'Santos', 'Reyes', 'Garcia', 'Ramos', 'Mendoza', 'Cruz', 'Torres', 'Gonzales', 'Villanueva',
    'Fernandez', 'Rivera', 'Aquino', 'Castillo', 'Castro', 'Perez', 'Sanchez', 'Romero', 'Lopez', 'Mercado',
    'Flores', 'Morales', 'Gutierrez', 'Ocampo', 'Silva', 'Bautista', 'Diaz', 'Martinez', 'Ramos', 'Santiago',
    'Navarro', 'Vargas', 'Jimenez', 'Salazar', 'Medina', 'Herrera', 'Cabrera', 'Vega', 'Sandoval', 'Cortez',
]
MIDDLE_INITIALS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'M', 'R', 'S', '']
PUROKS = ['Purok 1', 'Purok 2', 'Purok 3', 'Purok 4', 'Purok 5', 'Purok 6', 'Purok 7']
OCCUPATIONS = ['Farmer', 'Fisherman', 'Driver', 'Vendor', 'Laborer', 'Housewife', 'Student', 'Teacher', 'Barangay Staff', 'Self-employed', 'None']
CITIZENSHIPS = ['Filipino']
DIALECTS = ['Tagalog', 'Cuyonon', 'Waray', 'Cebuano', 'Ilocano', 'Bisaya']


class Command(BaseCommand):
    help = 'Create around 200 fake residents with random male/female, 4Ps, PWD, solo parent, senior, deceased, birth years.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=200,
            help='Number of residents to create (default 200)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all residents before creating (use with care)',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count = options['count']
        clear = options['clear']

        barangays = list(Barangay.objects.filter(is_active=True).order_by('id'))
        if not barangays:
            self.stdout.write(self.style.ERROR('No active barangays found. Create barangays first (Reference > Barangay).'))
            return

        if clear:
            n = Resident.objects.count()
            Resident.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {n} existing residents.'))

        self.stdout.write(f'Creating {count} fake residents across {len(barangays)} barangay(s)...')

        today = date.today()
        residents_created = 0

        # Choice lists from model
        civil_statuses = [c[0] for c in Resident.CIVIL_STATUS_CHOICES]
        education = [e[0] for e in Resident.EDUCATION_CHOICES]
        health_statuses = [h[0] for h in Resident.HEALTH_STATUS_CHOICES]
        economic_statuses = [e[0] for e in Resident.ECONOMIC_STATUS_CHOICES]

        # We'll assign some residents as PWD, 4PS, Solo Parent, Senior (by birth year), and some deceased
        for i in range(count):
            barangay = random.choice(barangays)
            is_male = random.choice([True, False])
            first = random.choice(FIRST_NAMES_MALE if is_male else FIRST_NAMES_FEMALE)
            last = random.choice(LAST_NAMES)
            middle = random.choice(MIDDLE_INITIALS)
            if middle:
                middlename = middle + '.'
            else:
                middlename = ''

            # Random birth year: 1940-2010 so we get seniors (60+) and young
            year = random.randint(1940, 2010)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            try:
                date_of_birth = date(year, month, day)
            except ValueError:
                date_of_birth = date(year, month, 1)

            # About 8% deceased
            status = Resident.STATUS_DECEASED if random.random() < 0.08 else Resident.STATUS_ALIVE
            gender = Resident.GENDER_MALE if is_male else Resident.GENDER_FEMALE

            # Economic status: weight 4PS, Solo Parent, Senior Citizen
            r = random.random()
            if r < 0.15:
                economic_status = '4PS MEMBER'
            elif r < 0.28:
                economic_status = 'SOLO PARENT'
            elif r < 0.42:
                economic_status = 'SENIOR CITIZEN'
            else:
                economic_status = random.choice([e for e in economic_statuses if e not in ('4PS MEMBER', 'SOLO PARENT', 'SENIOR CITIZEN')])

            # Health: about 12% PWD
            health_status = 'PWD' if random.random() < 0.12 else random.choice([h for h in health_statuses if h != 'PWD'])

            age = today.year - date_of_birth.year
            if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
                age -= 1
            # Ensure senior citizens are actually 60+
            if economic_status == 'SENIOR CITIZEN' and age < 60:
                date_of_birth = date(today.year - 65, month, min(day, 28))
            # Ensure 4Ps / solo can be any adult
            if economic_status == '4PS MEMBER' and age > 80:
                date_of_birth = date(today.year - random.randint(25, 50), month, min(day, 28))

            resident_id = ''  # let model save() auto-generate
            place_of_birth = random.choice(['Manila', 'Puerto Princesa', 'Quezon City', 'Cebu', 'Davao', 'Barangay Health Center'])
            address = f'{last} Residence, {random.choice(PUROKS)}'
            purok = random.choice(PUROKS)
            contact = '09' + ''.join([str(random.randint(0, 9)) for _ in range(9)])
            civil_status = random.choice(civil_statuses)
            educational_attainment = random.choice(education)
            citizenship = random.choice(CITIZENSHIPS)
            dialect_ethnic = random.choice(DIALECTS)
            occupation = random.choice(OCCUPATIONS)
            is_voter = random.choice([True, False])

            Resident.objects.create(
                resident_id=resident_id,
                barangay=barangay,
                status=status,
                lastname=last,
                firstname=first,
                middlename=middlename,
                suffix='',
                gender=gender,
                date_of_birth=date_of_birth,
                place_of_birth=place_of_birth,
                address=address,
                purok=purok,
                contact_no=contact,
                civil_status=civil_status,
                educational_attainment=educational_attainment,
                citizenship=citizenship,
                dialect_ethnic=dialect_ethnic,
                occupation=occupation,
                health_status=health_status,
                economic_status=economic_status,
                is_voter=is_voter,
                remarks='',
            )
            residents_created += 1

        self.stdout.write(self.style.SUCCESS(f'Created {residents_created} fake residents.'))
