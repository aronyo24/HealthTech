
from django.contrib import admin
from django.urls import path,include
from . import views
from clinic import views as clinic_views
urlpatterns = [
    path('', views.home, name='home'),

    
    path('about/', views.about, name='about'),
    path('departments/', views.departments, name='departments'),
    path('services/', views.services, name='services'),
    path('service-details/', views.service_details, name='service_details'),
    path('department-details/', views.department_details, name='department_details'),

    path('doctors/', views.doctors, name='doctors'),
    path('doctors/<slug:slug>/', views.doctor_detail, name='doctor_detail'),


    path('gallery/', views.gallery, name='gallery'),
    path('faq/', views.faq, name='faq'),


    path('contact/', views.contact, name='contact'),

    
]
