
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
    path('gallery/', views.gallery, name='gallery'),
    path('testimonials/', views.testimonials, name='testimonials'),
    path('faq/', views.faq, name='faq'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('starter-page/', views.starter_page, name='starter_page'),
    path('appointment/', views.appointment, name='appointment'),
    path('contact/', views.contact, name='contact'),
    path('404/', views.page_404, name='404'),
    
]
