from django.contrib import admin

from core.models import AthleteProfile, Event, Performance, Verification


# Performance displayed inside AthleteProfile
class PerformanceInline(admin.TabularInline):
    model = Performance
    extra = 0


class AthleteProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "date_of_birth",
        "gender",
        "phone_number",
        "county",
        "location",
        "is_verified",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "gender",
        "is_verified",
        "created_at",
        "updated_at",
    )

    inlines = [PerformanceInline]


class VerificationAdmin(admin.ModelAdmin):
    list_display = (
        "performance",
        "verified_by",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )


class EventAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "description",
    )

    list_filter = (
        "name",
        "description",
    )


class PerformanceAdmin(admin.ModelAdmin):
    list_display = (
        "athlete",
        "event",
        "result",
        "verification",
        "supporting_document",
    )

    list_filter = (
        "athlete",
        "event",
    )


# Register models
admin.site.register(AthleteProfile, AthleteProfileAdmin)
admin.site.register(Verification, VerificationAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Performance, PerformanceAdmin)


# Admin site branding
admin.site.site_header = "Athlete Management Admin"