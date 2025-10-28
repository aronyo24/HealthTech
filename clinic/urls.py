from django.urls import path
from . import views

app_name = "clinic"

urlpatterns = [

    path("register/", views.register, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("patient/dashboard/", views.patient_dashboard, name="patient_dashboard"),
    path("doctor/dashboard/", views.doctor_dashboard, name="doctor_dashboard"),
    path("appointments/book/", views.book_appointment, name="book_appointment"),
    path("appointments/<int:pk>/cancel-request/", views.request_appointment_cancellation, name="request_appointment_cancellation"),
    path("appointments/<int:pk>/status/", views.update_appointment_status, name="update_appointment_status"),
]
