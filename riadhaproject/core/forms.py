from django import forms
from django.contrib.auth.forms import UserCreationForm
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth.models import User
from .models import AthleteProfile, Event, Performance

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2',
        )


class AthleteProfileForm(forms.ModelForm):

    class Meta:
        model = AthleteProfile
        fields = (
            'date_of_birth',
            'gender',
            'phone_number',
            'county',
            'location',
            'profile_photo',
            'bio',
        )

        widgets = {
            'date_of_birth': forms.DateInput(
                attrs={'type': 'date'}
            ),

            'bio': forms.Textarea(
                attrs={
                    'rows': 4,
                    'placeholder': 'Tell us briefly about yourself...'
                }
            ),
        }

class RaceTimeWidget(forms.MultiWidget):
    """Three-part duration picker that supports races lasting many hours."""

    template_name = 'core/widgets/race_time.html'

    def __init__(self, attrs=None):
        widgets = (
            forms.NumberInput(attrs={
                'min': 0,
                'max': 9999,
                'step': 1,
                'placeholder': '0',
                'aria-label': 'Hours',
                'class': 'w-full rounded-lg border border-slate-300 px-3 py-2',
            }),
            forms.NumberInput(attrs={
                'min': 0,
                'max': 59,
                'step': 1,
                'placeholder': '0',
                'aria-label': 'Minutes',
                'class': 'w-full rounded-lg border border-slate-300 px-3 py-2',
            }),
            forms.NumberInput(attrs={
                'min': 0,
                'max': 59.99,
                'step': '0.01',
                'placeholder': '0.00',
                'aria-label': 'Seconds',
                'class': 'w-full rounded-lg border border-slate-300 px-3 py-2',
            }),
        )
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value is None or value == '':
            return [None, None, None]

        total_centiseconds = int(
            (Decimal(str(value)) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        )
        hours, remainder = divmod(total_centiseconds, 360000)
        minutes, remainder = divmod(remainder, 6000)
        seconds = Decimal(remainder) / 100
        return [hours, minutes, seconds]


class RaceTimeField(forms.MultiValueField):
    """Accept hours, minutes, and seconds; store the combined total seconds."""

    def __init__(self, *args, **kwargs):
        fields = (
            forms.IntegerField(min_value=0, max_value=9999, required=False),
            forms.IntegerField(min_value=0, max_value=59, required=False),
            forms.DecimalField(
                min_value=Decimal('0'),
                max_value=Decimal('59.99'),
                max_digits=4,
                decimal_places=2,
                required=False,
            ),
        )
        kwargs.setdefault('label', 'Race time')
        kwargs.setdefault('help_text', 'Choose hours, minutes, and seconds. Seconds support hundredths.')
        super().__init__(
            *args,
            fields=fields,
            widget=RaceTimeWidget(),
            require_all_fields=False,
            **kwargs,
        )

    def compress(self, values):
        if not values or not any(value is not None for value in values):
            return None
        hours, minutes, seconds = (value if value is not None else 0 for value in values)
        total_seconds = Decimal(hours * 3600 + minutes * 60) + Decimal(seconds)
        if total_seconds <= 0:
            raise forms.ValidationError('Race time must be greater than zero.')
        return total_seconds


class PerformanceForm(forms.ModelForm):
    result = RaceTimeField()

    class Meta:
        model = Performance
        fields = (
            'event',
            'result',
            'competition_name',
            'supporting_document',
            'competition_date',
        )

        widgets = {
            'competition_date': forms.DateInput(
                attrs={'type': 'date'}
            ),

            'competition_name': forms.TextInput(
                attrs={
                    'placeholder': 'Example: County Championships'
                }
            ),
            'supporting_document': forms.ClearableFileInput(
                attrs={
                    'accept': '.pdf,.jpg,.jpeg,.png'
                }
            )
        }