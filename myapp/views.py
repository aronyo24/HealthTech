from datetime import timedelta

from django.shortcuts import get_object_or_404, render
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.contrib import messages

from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.utils import timezone
from django.utils.text import slugify

from clinic.forms import TIME_SLOT_CHOICES
from clinic.models import Appointment, Doctor

# Create your views here.
def home(request):
    return render(request, 'index.html')
def about(request):
    return render(request, 'about.html')
def services(request):
    return render(request, 'services.html')
def service_details(request):
    return render(request, 'service-details.html')
def gallery(request):
    return render(request, 'gallery.html')
def testimonials(request):
    return render(request, 'testimonials.html')
def faq(request):
    return render(request, 'faq.html')
def privacy(request):
    return render(request, 'privacy.html')
def terms(request):
    return render(request, 'terms.html')
def starter_page(request):
    return render(request, 'starter-page.html')   
def departments(request):
    return render(request, 'departments.html')

def doctors(request):
    doctors_qs = Doctor.objects.select_related("user").order_by("name")

    doctors = []
    departments = []
    seen_departments = set()
    seen_locations = set()
    locations = []

    for doctor in doctors_qs:
        department_label = doctor.department or doctor.specialization or "General Practice"
        department_slug = slugify(department_label) or "general-practice"

        doctor.department_label = department_label
        doctor.department_slug = department_slug
        doctor.display_title = doctor.title or doctor.specialization
        doctor.display_credentials = doctor.qualifications

        card_description = doctor.short_bio or doctor.bio
        if card_description and len(card_description) > 160:
            card_description = f"{card_description[:157].rstrip()}..."
        doctor.card_description = card_description

        doctor.experience_label = (
            f"{doctor.years_of_experience}+ Years Experience"
            if doctor.years_of_experience
            else ""
        )

        doctor.highlight_items = [item.strip() for item in doctor.profile_highlights.splitlines() if item.strip()]
        doctor.schedule_items = [item.strip() for item in doctor.schedule_notes.splitlines() if item.strip()]

        if department_slug not in seen_departments:
            departments.append({"name": department_label, "slug": department_slug})
            seen_departments.add(department_slug)

        if doctor.location and doctor.location not in seen_locations:
            locations.append(doctor.location)
            seen_locations.add(doctor.location)

        doctors.append(doctor)

    featured_doctor = next((doc for doc in doctors if doc.is_featured), doctors[0] if doctors else None)
    tab_doctor = featured_doctor or (doctors[0] if doctors else None)

    context = {
        "doctors": doctors,
        "departments": departments,
        "locations": locations,
        "featured_doctor": featured_doctor,
        "tab_doctor": tab_doctor,
        "recent_doctors": doctors[:6],
    }

    return render(request, 'doctors.html', context)


def doctor_detail(request, slug):
    doctor = get_object_or_404(Doctor.objects.select_related("user"), slug=slug)

    department_label = doctor.department or doctor.specialization or "General Practice"
    doctor.department_label = department_label
    doctor.display_title = doctor.title or doctor.specialization
    doctor.display_credentials = doctor.qualifications
    doctor.experience_label = (
        f"{doctor.years_of_experience}+ Years Experience" if doctor.years_of_experience else ""
    )
    doctor.highlight_items = [item.strip() for item in doctor.profile_highlights.splitlines() if item.strip()]
    doctor.schedule_items = [item.strip() for item in doctor.schedule_notes.splitlines() if item.strip()]

    today = timezone.localdate()
    date_window = [today + timedelta(days=i) for i in range(7)]
    slot_label_map = {slot: label for slot, label in TIME_SLOT_CHOICES}

    booked_pairs = (
        Appointment.objects.filter(doctor=doctor, appointment_date__in=date_window)
        .exclude(status__in=("Cancelled",))
        .values_list("appointment_date", "time_slot")
    )

    booked_map = {}
    for appointment_date, time_slot in booked_pairs:
        booked_map.setdefault(appointment_date, set()).add(time_slot)

    availability_window = []
    for day in date_window:
        day_booked = booked_map.get(day, set())
        available_slots = [
            {"value": slot, "label": slot_label_map.get(slot, slot)}
            for slot, _ in TIME_SLOT_CHOICES
            if slot not in day_booked
        ]
        slot_preview = available_slots[:6]
        availability_window.append(
            {
                "date": day,
                "label": day.strftime("%A, %b %d"),
                "slots": slot_preview,
                "remaining": max(len(available_slots) - len(slot_preview), 0),
                "has_slots": bool(available_slots),
            }
        )

    upcoming_appointments = (
        Appointment.objects.filter(doctor=doctor, appointment_date__gte=today)
        .exclude(status__in=("Cancelled",))
        .select_related("patient")
        .order_by("appointment_date", "time_slot")[:6]
    )

    for appt in upcoming_appointments:
        appt.time_label = slot_label_map.get(appt.time_slot, appt.time_slot)

    context = {
        "doctor": doctor,
        "availability_window": availability_window,
        "upcoming_appointments": upcoming_appointments,
    }

    return render(request, 'doctors_de.html', context)

def department_details(request):
    return render(request, 'department-details.html')

def appointment(request):
    return render(request, 'appointment.html')

def contact(request):
    return render(request, 'contact.html')

def page_404(request):
    # Render a friendly 404-like page — header links point to this name in the template
    return render(request, '404.html')

