from django.db import models
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

class MissingGoods(models.Model):
    STATUS_CHOICES = [
        ('missing', 'Missing'),
        ('found', 'Found'),
        ('safe', 'Safe'),
    ]
    CATEGORY_CHOICES = [
        ('electronics', 'Electronics'),
        ('vehicle', 'Vehicle'),
        ('document', 'Document'),
        ('jewelry', 'Jewelry'),
        ('other', 'Other'),
    ]
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, blank=True, null=True)
    description = models.TextField()
    image = models.ImageField(upload_to='missing_goods/',default='crime/static/img/icon.png')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='missing')
    last_seen = models.CharField(max_length=200)
    date_reported = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_category_display() if self.category else 'Uncategorized'})"

class UserCustom(AbstractUser):
    USER_TYPE_CHOICES = [
        ('investigating_officer', 'Investigating Officer'),
        ('front_line_officer', 'Front-line Officer'),
    ]

    phone_number = models.CharField(max_length=15, blank=True, null=True)
    gender = models.CharField(
        max_length=15,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('Others', 'Others')
        ],
        blank=True,
        null=True
    )
    email = models.EmailField(unique=True)
    user_type = models.CharField(
        max_length=30,
        choices=USER_TYPE_CHOICES,
    )

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

class CrimeCase(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Under Investigation'),
        ('closed', 'Closed'),
    ]
    case_id = models.CharField(max_length=100, unique=True)
    crime_type = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=100)
    date_reported = models.DateField(auto_now_add=True)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

class EvidenceFile(models.Model):
    crime_case = models.ForeignKey(CrimeCase, related_name='evidence', on_delete=models.CASCADE)
    file = models.FileField(upload_to='evidence/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

class WantedPerson(models.Model):
    STATUS_CHOICES = [
        ('at_large', 'At Large'),
        ('captured', 'Captured'),
    ]
    name = models.CharField(max_length=100)
    crime = models.CharField(max_length=200)
    reward = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='wanted/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='at_large')
    details = models.TextField(blank=True)

class Tip(models.Model):
    wanted_person = models.ForeignKey(WantedPerson, related_name='tips', on_delete=models.CASCADE)
    tip_text = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_anonymous = models.BooleanField(default=True)

class MissingPerson(models.Model):
    STATUS_CHOICES = [
        ('missing', 'Missing'),
        ('found', 'Found'),
        ('safe', 'Safe'),
    ]
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    details = models.TextField()
    image = models.ImageField(upload_to='missing/', default='crime/static/img/icon.png')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='missing')
    last_seen = models.CharField(max_length=200)
    date_reported = models.DateField(auto_now_add=True)

class MissingPersonReport(models.Model):
    missing_person = models.ForeignKey(MissingPerson, related_name='reports', on_delete=models.CASCADE)
    reporter_name = models.CharField(max_length=100)
    contact_info = models.CharField(max_length=200)
    details = models.TextField()
    approved = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

class PublicCrimeReport(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100)
    evidence = models.FileField(upload_to='public_reports/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_by = models.CharField(max_length=100)
    submitted_at = models.DateTimeField(auto_now_add=True)

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

class AnonymousTip(models.Model):
    tip_text = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

class Complaint(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

class CaseSuggestion(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    suggestion = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

class News(models.Model):
    photo = models.ImageField(upload_to='news/', default='crime/static/img/logo.jpeg')
    date = models.DateField()  # Use DateField for calendar widget
    title = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.title

class Report(models.Model):
    REPORT_TYPE_CHOICES = [
        ('photo', 'Photo'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('link', 'Link'),
        ('file', 'File'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Under Investigation'),
        ('closed', 'Closed'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    report_type = models.CharField(max_length=10, choices=REPORT_TYPE_CHOICES)
    file = models.FileField(upload_to='reports/', blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    def __str__(self):
        return f"{self.get_report_type_display()} Report by {self.user if self.user else 'Anonymous'} on {self.submitted_at.strftime('%Y-%m-%d')}"

