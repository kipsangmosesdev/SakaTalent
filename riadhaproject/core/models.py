from django.db import models
from django.contrib.auth.models import User

class AthleteProfile(models.Model):

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    COUNTY_CHOICES = [
        ('baringo', 'Baringo'),
        ('bomet', 'Bomet'),
        ('bungoma', 'Bungoma'),
        ('busia', 'Busia'),
        ('elgeyo-marakwet', 'Elgeyo-Marakwet'),
        ('embu', 'Embu'),
        ('garissa', 'Garissa'),
        ('homa-bay', 'Homa Bay'),
        ('isiolo', 'Isiolo'),
        ('kajiado', 'Kajiado'),
        ('kakamega', 'Kakamega'),
        ('kericho', 'Kericho'),
        ('kiambu', 'Kiambu'),
        ('kilifi', 'Kilifi'),
        ('kirinyaga', 'Kirinyaga'),
        ('kisii', 'Kisii'),
        ('kisumu', 'Kisumu'),
        ('kitui', 'Kitui'),
        ('kwale', 'Kwale'),
        ('laikipia', 'Laikipia'),
        ('lamu', 'Lamu'),
        ('machakos', 'Machakos'),
        ('makueni', 'Makueni'),
        ('mandera', 'Mandera'),
        ('meru', 'Meru'),
        ('migori', 'Migori'),
        ('marsabit', 'Marsabit'),
        ('mombasa', 'Mombasa'),
        ('murang\'a', 'Murang\'a'),
        ('nairobi', 'Nairobi'),
        ('nakuru', 'Nakuru'),
        ('nandi', 'Nandi'),
        ('narok', 'Narok'),
        ('nyamira', 'Nyamira'),
        ('nyandarua', 'Nyandarua'),
        ('nyeri', 'Nyeri'),
        ('samburu', 'Samburu'),
        ('siaya', 'Siaya'),
        ('taita-taveta', 'Taita-Taveta'),
        ('tana-river', 'Tana River'),
        ('tharaka-nithi', 'Tharaka-Nithi'),
        ('trans-nzoia', 'Trans-Nzoia'),
        ('turkana', 'Turkana'),
        ('uasin-gishu', 'Uasin Gishu'),
        ('vihiga', 'Vihiga'),
    ]

    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='athlete_profile')
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone_number = models.CharField(max_length=20)
    county = models.CharField(max_length=100, choices=COUNTY_CHOICES)
    location = models.CharField(max_length=150)
    profile_photo = models.ImageField(upload_to='athletes/',blank=True,null=True)
    bio = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def get_event_average(self, event):
        performances = self.performances.filter(event=event,verification__status='APPROVED')
        if not performances.exists():
            return None
        total = sum(performance.result for performance in performances)
        return total / performances.count()

    def get_event_best_result(self, event):
        performances = self.performances.filter(event=event,verification__status='APPROVED')
        if not performances.exists():
            return None
        return min(performance.result for performance in performances)

    def get_verified_race_count(self, event):
        return self.performances.filter(event=event,verification__status='APPROVED').count()


class Event(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    def get_event_average(self, event):
        performances = self.performances.filter(event=event,verification__status='APPROVED')
        if not performances.exists():
            return None
        total = sum(performance.result for performance in performances)
        return total / performances.count()


    def get_event_best_result(self, event):
        performances = self.performances.filter(event=event,verification__status='APPROVED')
        if not performances.exists():
            return None
        return min(performance.result for performance in performances)


class Performance(models.Model):
    athlete = models.ForeignKey(AthleteProfile,on_delete=models.CASCADE,related_name='performances')
    event = models.ForeignKey(Event,on_delete=models.CASCADE,related_name='performances')
    # Store total elapsed seconds so old data and numeric ranking stay compatible.
    # The form accepts hours/minutes/seconds and converts them before saving.
    result = models.DecimalField(max_digits=10,decimal_places=2)
    competition_name = models.CharField(max_length=150)
    competition_date = models.DateField()
    supporting_document = models.FileField(upload_to='supporting_documents/',blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.athlete} - "
            f"{self.event} - "
            f"{self.result}"
        )

class Verification(models.Model):

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    performance = models.OneToOneField(Performance,on_delete=models.CASCADE,related_name='verification')
    verified_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name='performance_verifications')
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='PENDING')
    comments = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.performance} - {self.status}"


class TrainingPlan(models.Model):
    """An athlete's preparation plan for an upcoming county championship."""

    athlete = models.OneToOneField(
        AthleteProfile,
        on_delete=models.CASCADE,
        related_name='training_plan',
    )
    championship_date = models.DateField()
    competition_description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.athlete} — County Championship {self.championship_date}"


class TrainingTarget(models.Model):
    """A private, event-specific time goal in a training plan."""

    plan = models.ForeignKey(
        TrainingPlan,
        on_delete=models.CASCADE,
        related_name='targets',
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='training_targets')
    competition_description = models.CharField(max_length=200, blank=True)
    competition_date = models.DateField()
    # Like Performance.result, store the entered race time as total seconds.
    target_result = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('event__name',)
        constraints = [
            models.UniqueConstraint(
                fields=('plan', 'event', 'competition_date'),
                name='unique_training_target_per_event_date',
            ),
        ]

    def __str__(self):
        return f"{self.plan.athlete} — {self.event}: {self.target_result}s target"


class TrainingResult(models.Model):
    """An athlete-recorded practice result; deliberately separate from Performance."""

    target = models.ForeignKey(
        TrainingTarget,
        on_delete=models.CASCADE,
        related_name='training_results',
    )
    training_date = models.DateField()
    result = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-training_date', '-created_at')

    def __str__(self):
        return f"{self.target.event} training result — {self.result}s on {self.training_date}"
