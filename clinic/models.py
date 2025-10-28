from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.text import slugify

ROLE_CHOICES = (
    ("admin", "Admin"),
    ("doctor", "Doctor"),
    ("patient", "Patient"),
)

class User(AbstractUser):
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="patient")

    def is_doctor(self):
        return self.role == "doctor"

    def is_patient(self):
        return self.role == "patient"


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor_profile")
    name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    title = models.CharField(max_length=150, blank=True, default="")
    qualifications = models.CharField(max_length=200, blank=True, default="")
    department = models.CharField(max_length=120, blank=True, default="")
    location = models.CharField(max_length=120, blank=True, default="")
    highlight = models.CharField(max_length=120, blank=True, default="")
    short_bio = models.TextField(blank=True, default="")
    bio = models.TextField(blank=True, default="")
    years_of_experience = models.PositiveIntegerField(null=True, blank=True)
    availability = models.CharField(max_length=150, blank=True, default="")
    profile_highlights = models.TextField(blank=True, default="")
    schedule_notes = models.TextField(blank=True, default="")
    review_summary = models.CharField(max_length=200, blank=True, default="")
    photo = models.ImageField(upload_to="doctor_photos/", blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    slug = models.SlugField(max_length=160, unique=True, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.specialization})"

    class Meta:
        ordering = ["name"]

    @property
    def primary_department(self):
        return self.department or self.specialization

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or slugify(self.specialization) or "doctor"
            slug_candidate = base_slug
            counter = 1
            while Doctor.objects.filter(slug=slug_candidate).exclude(pk=self.pk).exists():
                counter += 1
                slug_candidate = f"{base_slug}-{counter}"
            self.slug = slug_candidate
        super().save(*args, **kwargs)


class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient_profile")
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    contact = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.name


STATUS_CHOICES = (
    ("Pending", "Pending"),
    ("Confirmed", "Confirmed"),
    ("Completed", "Completed"),
    ("Cancelled", "Cancelled"),
    ("Cancel Requested", "Cancel Requested"),
)

class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    appointment_date = models.DateField()
    time_slot = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.patient} → {self.doctor} ({self.appointment_date})"
