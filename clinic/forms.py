from django import forms
from django.utils import timezone

from .models import Appointment, Doctor

TIME_SLOT_CHOICES = [
    ("09:00 - 09:30", "09:00 - 09:30 AM"),
    ("09:30 - 10:00", "09:30 - 10:00 AM"),
    ("10:00 - 10:30", "10:00 - 10:30 AM"),
    ("10:30 - 11:00", "10:30 - 11:00 AM"),
    ("11:00 - 11:30", "11:00 - 11:30 AM"),
    ("11:30 - 12:00", "11:30 - 12:00 PM"),
    ("12:00 - 12:30", "12:00 - 12:30 PM"),
    ("12:30 - 13:00", "12:30 - 01:00 PM"),
    ("13:00 - 13:30", "01:00 - 01:30 PM"),
    ("13:30 - 14:00", "01:30 - 02:00 PM"),
    ("14:00 - 14:30", "02:00 - 02:30 PM"),
    ("14:30 - 15:00", "02:30 - 03:00 PM"),
]


class AppointmentForm(forms.ModelForm):
    time_slot = forms.ChoiceField(choices=TIME_SLOT_CHOICES, label="Preferred time")

    class Meta:
        model = Appointment
        fields = ["doctor", "appointment_date", "time_slot"]
        widgets = {
            "appointment_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, patient=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.patient = patient

        self.fields["doctor"].queryset = Doctor.objects.order_by("name")
        self.fields["doctor"].empty_label = "Select a doctor"

        today = timezone.localdate()
        self.fields["appointment_date"].widget.attrs["min"] = today.isoformat()

        self.fields["doctor"].widget.attrs.update({
            "class": "form-select form-select-lg",
        })
        self.fields["appointment_date"].widget.attrs.update({
            "class": "form-control form-control-lg",
        })
        self.fields["time_slot"].widget.attrs.update({
            "class": "form-select form-select-lg",
        })

    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get("appointment_date")
        if appointment_date and appointment_date < timezone.localdate():
            raise forms.ValidationError("Appointment date cannot be in the past.")
        return appointment_date

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get("doctor")
        appointment_date = cleaned_data.get("appointment_date")
        time_slot = cleaned_data.get("time_slot")

        if doctor and appointment_date and time_slot:
            conflict = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                time_slot=time_slot,
            ).exclude(status="Cancelled")
            if self.instance.pk:
                conflict = conflict.exclude(pk=self.instance.pk)

            if conflict.exists():
                self.add_error("time_slot", "That time slot is already booked for the selected doctor.")

        return cleaned_data
