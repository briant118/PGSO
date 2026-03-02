from django.db import models
from reference.models import Barangay, Position


class Resident(models.Model):
    """Model for resident records."""
    
    # Status choices
    STATUS_ALIVE = 'ALIVE'
    STATUS_DECEASED = 'DECEASED'
    STATUS_CHOICES = [
        (STATUS_ALIVE, 'Alive'),
        (STATUS_DECEASED, 'Deceased'),
    ]
    
    # Gender choices
    GENDER_MALE = 'MALE'
    GENDER_FEMALE = 'FEMALE'
    GENDER_CHOICES = [
        (GENDER_MALE, 'Male'),
        (GENDER_FEMALE, 'Female'),
    ]
    
    # Civil Status choices
    CIVIL_STATUS_CHOICES = [
        ('SINGLE', 'Single'),
        ('MARRIED', 'Married'),
        ('WIDOW', 'Widow'),
        ('SEPARATED', 'Separated'),
        ('LIVE-IN', 'Live-In'),
    ]
    
    # Educational Attainment choices
    EDUCATION_CHOICES = [
        ('DAY CARE STUDENT', 'Day Care Student'),
        ('ELEMENTARY LEVEL', 'Elementary Level'),
        ('ELEMENTARY GRADUATE', 'Elementary Graduate'),
        ('HIGH SCHOOL LEVEL', 'High School Level'),
        ('HIGH SCHOOL GRADUATE', 'High School Graduate'),
        ('COLLEGE LEVEL', 'College Level'),
        ('COLLEGE GRADUATE', 'College Graduate'),
        ('VOCATIONAL GRADUATE', 'Vocational Graduate'),
        ('POST GRADUATE', 'Post Graduate'),
        ('ALTERNATIVE LEARNING SYSTEM', 'Alternative Learning System'),
    ]
    
    # Health Status choices
    HEALTH_STATUS_CHOICES = [
        ('PWD', 'PWD'),
        ('SMOKER', 'Smoker'),
        ('HYPERTENSION', 'Hypertension'),
        ('DIABETIC', 'Diabetic'),
        ('MENTAL HEALTH', 'Mental Health'),
        ('HEALTHY', 'Healthy'),
    ]
    
    # Economic Status choices
    ECONOMIC_STATUS_CHOICES = [
        ('SOLO PARENT', 'Solo Parent'),
        ('SENIOR CITIZEN', 'Senior Citizen'),
        ('NHTS MEMBER', 'NHTS Member'),
        ('4PS MEMBER', '4PS Member'),
        ('OUT OF SCHOOL', 'Out of School'),
        ('IN SCHOOL', 'In School'),
        ('WITH BUSINESS', 'With Business'),
    ]
    
    # Basic Information
    resident_id = models.CharField(max_length=20, unique=True, blank=True)
    profile_picture = models.ImageField(upload_to='residents/', blank=True, null=True)
    barangay = models.ForeignKey(Barangay, on_delete=models.PROTECT, related_name='residents')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ALIVE)
    
    # Name fields
    lastname = models.CharField(max_length=100)
    firstname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100, blank=True)
    suffix = models.CharField(max_length=20, blank=True)
    
    # Personal Information
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=200)
    
    # Contact Information
    address = models.CharField(max_length=200)
    purok = models.CharField(max_length=50)
    contact_no = models.CharField(max_length=50)
    
    # Additional Information
    civil_status = models.CharField(max_length=20, choices=CIVIL_STATUS_CHOICES)
    educational_attainment = models.CharField(max_length=50, choices=EDUCATION_CHOICES)
    citizenship = models.CharField(max_length=100)
    dialect_ethnic = models.CharField(max_length=100)
    occupation = models.CharField(max_length=100)
    health_status = models.CharField(max_length=50, choices=HEALTH_STATUS_CHOICES)
    economic_status = models.CharField(max_length=50, choices=ECONOMIC_STATUS_CHOICES)
    
    # Other fields
    is_voter = models.BooleanField(default=False)
    precinct_number = models.CharField(max_length=20, blank=True, help_text='Precinct number for voter registration')
    voter_legend = models.CharField(
        max_length=20,
        blank=True,
        help_text='Voter legend: comma-separated A=Illiterate, B=PWD, C=Senior (e.g. A,B or A,B,C)',
    )
    date_verified = models.DateField(null=True, blank=True, help_text='Date the voter record was verified')
    verified_by = models.CharField(max_length=150, blank=True, help_text='Name or username of person who verified')
    remarks = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['id']
        verbose_name = 'Resident'
        verbose_name_plural = 'Residents'
    
    def __str__(self):
        return f"{self.firstname} {self.lastname}"
    
    LEGEND_LABELS = {'A': 'Illiterate', 'B': 'PWD', 'C': 'Senior'}

    def get_voter_legend_display(self):
        """Return display string for voter_legend (supports multiple: A,B,C -> 'Illiterate, PWD, Senior')."""
        if not self.voter_legend or not self.voter_legend.strip():
            return '—'
        codes = [c.strip() for c in self.voter_legend.split(',') if c.strip()]
        return ', '.join(self.LEGEND_LABELS.get(c, c) for c in codes) or '—'

    def get_full_name(self):
        """Returns the full name with suffix if available."""
        parts = [self.firstname, self.middlename, self.lastname]
        name = ' '.join(filter(None, parts))
        if self.suffix:
            name += f" {self.suffix}"
        return name
    
    def get_age(self):
        """Calculate and return the current age."""
        from datetime import date
        today = date.today()
        age = today.year - self.date_of_birth.year
        if today.month < self.date_of_birth.month or (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
            age -= 1
        return age
    
    def save(self, *args, **kwargs):
        """Override save to auto-generate resident ID.

        Format rules:
        - 1 to 99,999  -> zero-padded 5 digits, e.g. 00001, 00002, ..., 99999
        - 100,000+     -> letter prefix for each 100k block, then 4 digits:
          100,000..199,999 -> A0001, A0002, ...
          200,000..299,999 -> B0001, B0002, ...
        """
        if not self.resident_id:
            # Use last primary key as sequence source
            last_resident = Resident.objects.order_by('-id').first()
            next_seq = (last_resident.id if last_resident else 0) + 1

            if next_seq <= 99999:
                # Simple zero-padded numeric ID up to 99,999
                self.resident_id = f"{next_seq:05d}"
            else:
                # Use letter prefix per 100k block, then 4-digit sequence inside the block
                # 100,000..199,999 -> 'A', 200,000..299,999 -> 'B', etc.
                block_index = (next_seq - 100000) // 100000  # 0-based
                letter = chr(ord('A') + block_index)
                within_block = (next_seq - 100000) % 100000 + 1  # 1..100000
                within_block = min(within_block, 9999)  # keep 4 digits max
                self.resident_id = f"{letter}{within_block:04d}"
        super().save(*args, **kwargs)


class BarangayOfficial(models.Model):
    """Model for barangay officials."""
    
    resident = models.ForeignKey(Resident, on_delete=models.PROTECT, related_name='official_positions')
    barangay = models.ForeignKey(Barangay, on_delete=models.PROTECT, related_name='officials')
    position = models.ForeignKey(Position, on_delete=models.PROTECT, related_name='officials')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    remarks = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Barangay Official'
        verbose_name_plural = 'Barangay Officials'
        # Ensure a resident can only have one active position per barangay
        unique_together = [['resident', 'barangay', 'position', 'is_active']]
    
    def __str__(self):
        return f"{self.resident.get_full_name()} - {self.position.name} ({self.barangay.name})"


class CoordinatorPosition(models.Model):
    """Positions for coordinators only (separate from reference Position management)."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code', 'name']
        verbose_name = 'Coordinator Position'
        verbose_name_plural = 'Coordinator Positions'

    def __str__(self):
        return self.name


class Coordinator(models.Model):
    """Coordinator record (barangay coordinator with position, contact, etc.)."""
    barangay = models.ForeignKey(Barangay, on_delete=models.PROTECT, related_name='coordinators')
    fullname = models.CharField(max_length=200)
    position = models.ForeignKey(CoordinatorPosition, on_delete=models.PROTECT, related_name='coordinators')
    contact_no = models.CharField(max_length=50, blank=True)
    remarks = models.TextField(blank=True)
    date_start = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['barangay', 'fullname']
        verbose_name = 'Coordinator'
        verbose_name_plural = 'Coordinators'

    def __str__(self):
        return f"{self.fullname} – {self.position.name}"
