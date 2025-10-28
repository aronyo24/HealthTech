from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Doctor, Patient, Appointment

class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (("Role", {"fields": ("role",)}),)

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("name", "primary_department", "location", "is_featured")
    list_filter = ("department", "is_featured")
    search_fields = ("name", "specialization", "department", "location")
    autocomplete_fields = ("user",)
    readonly_fields = ("slug",)
    fieldsets = (
        (
            "Linked User",
            {"fields": ("user", "is_featured", "slug")},
        ),
        (
            "Professional Details",
            {
                "fields": (
                    "name",
                    "specialization",
                    "department",
                    "title",
                    "qualifications",
                    "years_of_experience",
                    "availability",
                    "location",
                    "highlight",
                )
            },
        ),
        (
            "Profile Content",
            {
                "fields": (
                    "photo",
                    "short_bio",
                    "bio",
                    "profile_highlights",
                    "schedule_notes",
                    "review_summary",
                )
            },
        ),
    )


admin.site.register(User, UserAdmin)
admin.site.register(Patient)
admin.site.register(Appointment)
