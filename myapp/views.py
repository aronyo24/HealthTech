from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.contrib import messages

from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie

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
    return render(request, 'doctors.html')

def department_details(request):
    return render(request, 'department-details.html')

def appointment(request):
    return render(request, 'appointment.html')

def contact(request):
    return render(request, 'contact.html')

def page_404(request):
    # Render a friendly 404-like page — header links point to this name in the template
    return render(request, '404.html')

