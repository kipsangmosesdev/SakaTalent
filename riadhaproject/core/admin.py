from django.contrib import admin

from core.models import (
    AthleteProfile,
    Event,
    Performance,
    TrainingPlan,
    TrainingResult,
    TrainingTarget,
    Verification,
)


class PerformanceInline(admin.TabularInline):
    model = Performance
    extra = 0
    fields = (
        'event', 'result', 'competition_name', 'competition_date',
        'verification_status', 'supporting_document', 'created_at',
    )
    readonly_fields = ('verification_status', 'created_at')
    autocomplete_fields = ('event',)
    show_change_link = True
    ordering = ('-competition_date', '-created_at')

    @admin.display(description='Verification')
    def verification_status(self, performance):
        try:
            return performance.verification.get_status_display()
        except Verification.DoesNotExist:
            return 'Not submitted'


class TrainingPlanInline(admin.StackedInline):
    model = TrainingPlan
    extra = 0
    fields = ('championship_date', 'competition_description', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    show_change_link = True


@admin.register(AthleteProfile)
class AthleteProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'date_of_birth', 'gender', 'phone_number', 'county',
        'location', 'is_verified', 'created_at',
    )
    list_filter = ('gender', 'county', 'is_verified', 'created_at')
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name',
        'user__email', 'phone_number', 'county', 'location',
    )
    list_select_related = ('user',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Athlete account', {'fields': ('user', 'is_verified')}),
        ('Profile', {'fields': ('date_of_birth', 'gender', 'phone_number', 'county', 'location', 'profile_photo', 'bio')}),
        ('Record dates', {'fields': ('created_at', 'updated_at')}),
    )
    inlines = (PerformanceInline, TrainingPlanInline)


class VerificationInline(admin.StackedInline):
    model = Verification
    extra = 0
    fields = ('status', 'verified_by', 'comments', 'verified_at', 'created_at')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('verified_by',)


@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = (
        'athlete', 'event', 'result', 'competition_name', 'competition_date',
        'verification_status', 'created_at',
    )
    list_filter = ('event', 'competition_date', 'verification__status')
    search_fields = (
        'athlete__user__username', 'athlete__user__first_name',
        'athlete__user__last_name', 'event__name', 'competition_name',
    )
    list_select_related = ('athlete__user', 'event')
    date_hierarchy = 'competition_date'
    autocomplete_fields = ('athlete', 'event')
    readonly_fields = ('created_at',)
    inlines = (VerificationInline,)

    @admin.display(description='Verification', ordering='verification__status')
    def verification_status(self, performance):
        try:
            return performance.verification.get_status_display()
        except Verification.DoesNotExist:
            return 'Not submitted'


class TrainingTargetInline(admin.TabularInline):
    model = TrainingTarget
    extra = 0
    fields = ('event', 'target_result', 'competition_description', 'competition_date', 'created_at')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('event',)
    show_change_link = True
    ordering = ('-competition_date', '-created_at')


@admin.register(TrainingPlan)
class TrainingPlanAdmin(admin.ModelAdmin):
    list_display = ('athlete', 'championship_date', 'competition_description', 'updated_at')
    search_fields = ('athlete__user__username', 'athlete__user__first_name', 'athlete__user__last_name')
    list_select_related = ('athlete__user',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = (TrainingTargetInline,)


class TrainingResultInline(admin.TabularInline):
    model = TrainingResult
    extra = 0
    fields = ('training_date', 'result', 'notes', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('-training_date', '-created_at')


@admin.register(TrainingTarget)
class TrainingTargetAdmin(admin.ModelAdmin):
    list_display = (
        'athlete_name', 'event', 'target_result', 'competition_description',
        'competition_date', 'created_at',
    )
    list_filter = ('event', 'competition_date')
    search_fields = (
        'plan__athlete__user__username', 'plan__athlete__user__first_name',
        'plan__athlete__user__last_name', 'event__name', 'competition_description',
    )
    list_select_related = ('plan__athlete__user', 'event')
    autocomplete_fields = ('plan', 'event')
    readonly_fields = ('created_at',)
    inlines = (TrainingResultInline,)

    @admin.display(description='Athlete', ordering='plan__athlete__user__last_name')
    def athlete_name(self, target):
        return target.plan.athlete


@admin.register(TrainingResult)
class TrainingResultAdmin(admin.ModelAdmin):
    list_display = ('athlete_name', 'event_name', 'training_date', 'result', 'notes', 'created_at')
    list_filter = ('training_date', 'target__event')
    search_fields = (
        'target__plan__athlete__user__username', 'target__plan__athlete__user__first_name',
        'target__plan__athlete__user__last_name', 'target__event__name', 'notes',
    )
    list_select_related = ('target__plan__athlete__user', 'target__event')
    autocomplete_fields = ('target',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'training_date'

    @admin.display(description='Athlete', ordering='target__plan__athlete__user__last_name')
    def athlete_name(self, result):
        return result.target.plan.athlete

    @admin.display(description='Event', ordering='target__event__name')
    def event_name(self, result):
        return result.target.event


@admin.register(Verification)
class VerificationAdmin(admin.ModelAdmin):
    list_display = ('athlete_name', 'performance', 'status', 'verified_by', 'verified_at', 'created_at')
    list_filter = ('status', 'created_at', 'verified_at')
    search_fields = (
        'performance__athlete__user__username', 'performance__athlete__user__first_name',
        'performance__athlete__user__last_name', 'performance__event__name',
        'performance__competition_name', 'comments',
    )
    list_select_related = ('performance__athlete__user', 'performance__event', 'verified_by')
    autocomplete_fields = ('performance', 'verified_by')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    @admin.display(description='Athlete', ordering='performance__athlete__user__last_name')
    def athlete_name(self, verification):
        return verification.performance.athlete


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


admin.site.site_header = 'Athlete Management Admin'
admin.site.site_title = 'Athlete Management'
admin.site.index_title = 'Athlete records'
