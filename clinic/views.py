from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import AppointmentForm, TIME_SLOT_CHOICES
from .models import Appointment, Doctor, Patient, User


def _dashboard_route_name(user):
    """Return the dashboard route name that matches the user's role."""
    if user.is_superuser:
        return "admin:index"
    if user.is_doctor():
        return "clinic:doctor_dashboard"
    if user.is_patient():
        return "clinic:patient_dashboard"
    return "clinic:login"


# ---------- Patient Registration ----------

def register(request):
    if request.user.is_authenticated:
        return redirect(_dashboard_route_name(request.user))

    form_data = {}

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        age = request.POST.get("age", "").strip()
        gender = request.POST.get("gender", "").strip()
        contact = request.POST.get("contact", "").strip()
        accept_terms = request.POST.get("terms")

        form_data = {
            "name": name,
            "username": username,
            "email": email,
            "age": age,
            "gender": gender,
            "contact": contact,
        }

        if not all([name, username, email, password, confirm_password]):
            messages.error(request, "Please fill in all required fields.")
        elif password != confirm_password:
            messages.error(request, "Passwords do not match.")
        elif len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
        elif not accept_terms:
            messages.error(request, "Please accept the terms of service to continue.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "That username is already taken.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "That email is already registered.")
        else:
            patient_kwargs = {
                "name": name,
                "gender": gender,
                "contact": contact,
            }

            if age:
                try:
                    patient_kwargs["age"] = int(age)
                except ValueError:
                    messages.error(request, "Age must be a whole number.")
                    return render(request, "clinic/register.html", {"form_data": form_data})

            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        role="patient",
                        first_name=name.split(" ")[0] if name else "",
                    )
                    Patient.objects.create(user=user, **patient_kwargs)
            except IntegrityError:
                messages.error(request, "We ran into a problem while creating your account. Please try again.")
            else:
                messages.success(request, "Registration successful! You can now log in.")
                return redirect("clinic:login")

    return render(request, "clinic/register.html", {"form_data": form_data})


# ---------- Login ----------

def login_user(request):
    if request.user.is_authenticated:
        return redirect(_dashboard_route_name(request.user))

    form_data = {}
    next_url = request.GET.get("next", "")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        next_url = request.POST.get("next", next_url)

        form_data = {"username": username}

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)

            return redirect(_dashboard_route_name(user))

        messages.error(request, "Invalid username or password.")

    return render(request, "clinic/login.html", {"form_data": form_data, "next": next_url})


# ---------- Patient Dashboard ----------

@login_required(login_url="clinic:login")
def patient_dashboard(request):
    if not request.user.is_patient():
        messages.error(request, "You do not have access to the patient dashboard.")
        return redirect(_dashboard_route_name(request.user))

    patient = getattr(request.user, "patient_profile", None)

    if patient is None:
        messages.error(request, "We could not find your patient profile. Please contact support.")
        logout(request)
        return redirect("clinic:login")

    appointments_qs = (
        Appointment.objects.filter(patient=patient)
        .select_related("doctor", "doctor__user")
        .order_by("-appointment_date", "-created_at")
    )

    slot_label_map = {slot: label for slot, label in TIME_SLOT_CHOICES}

    appointments = list(appointments_qs)
    for appt in appointments:
        appt.time_label = slot_label_map.get(appt.time_slot, appt.time_slot)

    today = timezone.localdate()
    upcoming_qs = (
        appointments_qs.filter(appointment_date__gte=today)
        .exclude(status="Cancelled")
        .order_by("appointment_date", "time_slot")
    )
    upcoming = []
    for appt in upcoming_qs[:5]:
        appt.time_label = slot_label_map.get(appt.time_slot, appt.time_slot)
        upcoming.append(appt)

    stats_totals = {
        "total": appointments_qs.count(),
        "confirmed": appointments_qs.filter(status="Confirmed").count(),
        "pending": appointments_qs.filter(status="Pending").count(),
        "completed": appointments_qs.filter(status="Completed").count(),
        "cancelled": appointments_qs.filter(status="Cancelled").count(),
    }

    context = {
        "patient": patient,
        "appointments": appointments,
        "upcoming": upcoming,
        "stats": stats_totals,
    }

    return render(request, "patient_dashboard.html", context)


# ---------- Doctor Dashboard ----------

@login_required(login_url="clinic:login")
def doctor_dashboard(request):
    if not request.user.is_doctor():
        messages.error(request, "You do not have access to the doctor dashboard.")
        return redirect(_dashboard_route_name(request.user))

    doctor = getattr(request.user, "doctor_profile", None)

    if doctor is None:
        messages.error(request, "We could not find your doctor profile. Please contact support.")
        logout(request)
        return redirect("clinic:login")

    appointments_qs = (
        Appointment.objects.filter(doctor=doctor)
        .select_related("patient", "patient__user")
        .order_by("appointment_date", "time_slot", "created_at")
    )

    slot_label_map = {slot: label for slot, label in TIME_SLOT_CHOICES}

    appointments = []
    for appt in appointments_qs:
        appt.time_label = slot_label_map.get(appt.time_slot, appt.time_slot)
        created_local = timezone.localtime(appt.created_at)
        appt.created_display_date = created_local.strftime("%b %d, %Y")
        appt.created_display_time = created_local.strftime("%I:%M %p").lstrip("0")
        appointments.append(appt)

    today = timezone.localdate()

    todays_appointments = [appt for appt in appointments if appt.appointment_date == today]
    todays_appointments.sort(key=lambda a: a.time_slot)

    recent_appointments = sorted(
        appointments,
        key=lambda a: (a.appointment_date, a.created_at),
        reverse=True,
    )

    pending_count = sum(1 for appt in appointments if appt.status == "Pending")

    ordered_slots = [slot for slot, _ in TIME_SLOT_CHOICES]
    time_slot_data = [{"value": slot, "label": slot_label_map.get(slot, slot)} for slot in ordered_slots]

    calendar_days = []
    calendar_days_json = []
    for offset in range(7):  # today + next 6 days (total 7 days)
        current_date = today + timedelta(days=offset)
        day_appts = [appt for appt in appointments if appt.appointment_date == current_date]

        status_key = None
        if any(appt.status == "Confirmed" for appt in day_appts):
            status_key = "confirmed"
        elif any(appt.status == "Pending" for appt in day_appts):
            status_key = "pending"

        calendar_days.append(
            {
                "date_obj": current_date,
                "status": status_key,
                "count": len(day_appts),
                "date_iso": current_date.isoformat(),
                "label": current_date.strftime("%a %d"),
                "month": current_date.strftime("%b"),
            }
        )
        calendar_days_json.append(
            {
                "date": current_date.isoformat(),
                "label": current_date.strftime("%A, %d %B"),
                "status": status_key or "empty",
                "count": len(day_appts),
                "appointments": [
                    {
                        "id": appt.pk,
                        "patient": appt.patient.name,
                        "time": appt.time_slot,
                        "time_label": appt.time_label,
                        "status": appt.status,
                        "contact": appt.patient.contact or "",
                    }
                    for appt in sorted(day_appts, key=lambda a: a.time_slot)
                ],
            }
        )

    context = {
        "doctor": doctor,
        "appointments": appointments,
        "recent_appointments": recent_appointments,
        "todays_appointments": todays_appointments,
        "calendar_days": calendar_days,
        "calendar_days_json": calendar_days_json,
        "time_slot_data": time_slot_data,
        "stats": {
            "total": appointments_qs.count(),
            "today": len(todays_appointments),
            "completed": appointments_qs.filter(status="Completed").count(),
            "pending": pending_count,
        },
    }

    return render(request, "doctor_dashboard.html", context)


# ---------- Session Helpers ----------

@login_required(login_url="clinic:login")
def logout_user(request):
    """Sign the user out and return them to the login screen."""
    logout(request)
    messages.info(request, "You have been signed out successfully.")
    return redirect("clinic:login")


# ---------- Appointment Booking ----------

@login_required(login_url="clinic:login")
def book_appointment(request):
    if not request.user.is_patient():
        messages.error(request, "Only patients can book appointments.")
        return redirect(_dashboard_route_name(request.user))

    patient = getattr(request.user, "patient_profile", None)

    if patient is None:
        messages.error(request, "We could not find your patient profile. Please contact support.")
        logout(request)
        return redirect("clinic:login")

    upcoming = (
        Appointment.objects.filter(
            patient=patient,
            status__in=("Confirmed", "Pending"),
            appointment_date__gte=timezone.localdate(),
        )
        .select_related("doctor")
        .order_by("appointment_date", "time_slot")
    )[:3]

    slot_label_map = {slot: label for slot, label in TIME_SLOT_CHOICES}
    for appt in upcoming:
        appt.time_label = slot_label_map.get(appt.time_slot, appt.time_slot)

    if request.method == "POST":
        form = AppointmentForm(request.POST, patient=patient)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = patient
            appointment.status = "Pending"
            appointment.save()
            messages.success(
                request,
                "Appointment booked with Dr. {} on {} at {}.".format(
                    appointment.doctor.name,
                    appointment.appointment_date.strftime("%b %d, %Y"),
                    slot_label_map.get(appointment.time_slot, appointment.time_slot),
                ),
            )
            return redirect("clinic:patient_dashboard")
    else:
        form = AppointmentForm(patient=patient)

    context = {
        "form": form,
        "patient": patient,
        "upcoming": upcoming,
        "has_doctors": Doctor.objects.exists(),
    }

    return render(request, "appointment_form.html", context)


# ---------- Appointment Status Updates ----------

@require_POST
@login_required(login_url="clinic:login")
def update_appointment_status(request, pk):
    if not request.user.is_doctor():
        messages.error(request, "Only doctors can manage appointment approvals.")
        return redirect(_dashboard_route_name(request.user))

    doctor = getattr(request.user, "doctor_profile", None)
    if doctor is None:
        messages.error(request, "We could not find your doctor profile. Please contact support.")
        logout(request)
        return redirect("clinic:login")

    appointment = get_object_or_404(Appointment, pk=pk, doctor=doctor)

    decision = request.POST.get("decision")
    if decision == "confirm":
        appointment.status = "Confirmed"
        appointment.save(update_fields=["status"])
        messages.success(
            request,
            "Appointment with {} on {} has been confirmed.".format(
                appointment.patient.name,
                appointment.appointment_date.strftime("%b %d, %Y"),
            ),
        )
    elif decision == "cancel":
        appointment.status = "Cancelled"
        appointment.save(update_fields=["status"])
        messages.info(
            request,
            "Appointment with {} on {} has been declined.".format(
                appointment.patient.name,
                appointment.appointment_date.strftime("%b %d, %Y"),
            ),
        )
    else:
        messages.error(request, "Unknown action. Please try again.")

    return redirect("clinic:doctor_dashboard")
