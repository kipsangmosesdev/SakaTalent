from django.contrib import messages
import json
import secrets
import urllib.parse
import urllib.request

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.crypto import get_random_string
from core.models import AthleteProfile, Event, Performance, Verification
from .forms import SignUpForm, AthleteProfileForm, PerformanceForm

def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('complete_profile')
    else:
        form = SignUpForm()
    return render(request, 'core/signup.html', {
        'form': form,
        'google_signup_enabled': bool(
            settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET
        ),
    })


def google_signup(request):
    """Start Google OpenID Connect signup using a session-bound state value."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        messages.error(request, 'Google signup is not configured yet.')
        return redirect('signup')

    state = secrets.token_urlsafe(32)
    request.session['google_signup_state'] = state
    callback = _google_callback_uri(request)
    query = urllib.parse.urlencode({
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': callback,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'prompt': 'select_account',
    })
    return redirect(f'https://accounts.google.com/o/oauth2/v2/auth?{query}')


def google_signup_callback(request):
    """Exchange Google's authorization code and validate the returned identity."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    expected_state = request.session.pop('google_signup_state', None)
    if not expected_state or not secrets.compare_digest(
        expected_state, request.GET.get('state', '')
    ):
        messages.error(request, 'Google signup could not be verified. Please try again.')
        return redirect('signup')
    if request.GET.get('error') or not request.GET.get('code'):
        messages.error(request, 'Google signup was cancelled or could not be completed.')
        return redirect('signup')

    callback = _google_callback_uri(request)
    payload = urllib.parse.urlencode({
        'code': request.GET['code'],
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': callback,
        'grant_type': 'authorization_code',
    }).encode()
    try:
        token_request = urllib.request.Request(
            'https://oauth2.googleapis.com/token', data=payload,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )
        with urllib.request.urlopen(token_request, timeout=10) as response:
            token_data = json.loads(response.read())
        id_token = token_data.get('id_token')
        if not id_token:
            raise ValueError('Missing Google ID token')
        verify_request = urllib.request.Request(
            'https://oauth2.googleapis.com/tokeninfo?id_token=' +
            urllib.parse.quote(id_token, safe='')
        )
        with urllib.request.urlopen(verify_request, timeout=10) as response:
            identity = json.loads(response.read())
        if (identity.get('aud') != settings.GOOGLE_CLIENT_ID
                or identity.get('iss') not in {'accounts.google.com', 'https://accounts.google.com'}
                or identity.get('email_verified') not in {True, 'true'}
                or not identity.get('email')):
            raise ValueError('Google identity did not pass validation')
    except Exception:
        messages.error(request, 'We could not verify your Google account. Please try again.')
        return redirect('signup')

    email = identity['email'].strip().lower()
    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        name = identity.get('name', '').strip().split(maxsplit=1)
        first_name = identity.get('given_name', name[0] if name else '')[:150]
        last_name = identity.get('family_name', name[1] if len(name) > 1 else '')[:150]
        base = (email.partition('@')[0] or 'athlete')[:120]
        username = base
        while User.objects.filter(username__iexact=username).exists():
            username = f'{base[:110]}_{get_random_string(8).lower()}'
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return redirect(
        'dashboard' if hasattr(user, 'athlete_profile') else 'complete_profile'
    )


def _google_callback_uri(request):
    """Use a configured public URL when TLS terminates at a reverse proxy."""
    return settings.GOOGLE_REDIRECT_URI or request.build_absolute_uri(
        reverse('google_signup_callback')
    )

@login_required
def complete_profile(request):
    profile = getattr(request.user, 'athlete_profile', None)
    if request.method == 'POST':
        if profile:
            form = AthleteProfileForm(request.POST, request.FILES, instance=profile)
        else:
            form = AthleteProfileForm(request.POST,request.FILES)
        if form.is_valid():
            athlete_profile = form.save(commit=False)
            athlete_profile.user = request.user
            athlete_profile.save()

            messages.success(
                request,
                'Your athlete profile has been updated.' if profile else
                'Your athlete profile has been completed successfully.'
            )

            return redirect('my_profile')

    else:

        if profile:
            form = AthleteProfileForm(instance=profile)
        else:
            form = AthleteProfileForm()

    return render(
        request,
        'core/complete_profile.html',
        {'form': form, 'is_editing': profile is not None}
    )


@login_required
def my_profile(request):
    athlete = getattr(request.user, 'athlete_profile', None)
    if athlete is None:
        return redirect('complete_profile')

    return render(request, 'core/profile.html', {'athlete': athlete})


@login_required
def dashboard(request):
    try:
        athlete = request.user.athlete_profile
    except AthleteProfile.DoesNotExist:
        return redirect('complete_profile')

    athlete_performances = Performance.objects.filter(athlete=athlete)
    performance_stats = athlete_performances.aggregate(
        total=Count('id'),
        verified=Count('id', filter=Q(verification__status='APPROVED')),
        pending=Count('id', filter=Q(verification__status='PENDING')),
    )
    performance_stats['events'] = athlete_performances.values('event_id').distinct().count()

    verified_performances = athlete_performances.filter(
        verification__status='APPROVED'
    ).select_related('event')

    event_ids = verified_performances.values_list(
        'event_id',
        flat=True
    ).distinct()

    events = Event.objects.filter(
        id__in=event_ids
    )

    rankings = []

    for event in events:
        ranking = get_athlete_ranking(
            athlete,
            event
        )

        if ranking:
            rankings.append({
                'event': event,
                'average': ranking['average'],
                'best': ranking['best'],
                'races': ranking['races'],
                'position': ranking['position'],
            })

    return render(
        request,
        'core/dashboard.html',
        {
            'athlete': athlete,
            'rankings': rankings,
            'performance_stats': performance_stats,
        }
    )


@login_required
def add_performance(request):
    try:
        athlete = request.user.athlete_profile
    except AthleteProfile.DoesNotExist:
        return redirect('complete_profile')

    if request.method == 'POST':
        form = PerformanceForm(request.POST, request.FILES)

        if form.is_valid():
            performance = form.save(commit=False)
            performance.athlete = athlete
            performance.save()
            Verification.objects.create(performance=performance)

            messages.success(
                request,
                'Performance added successfully.'
            )

            return redirect('my_performances')

    else:
        form = PerformanceForm()

    return render(
        request,
        'core/add_performance.html',
        {'form': form}
    )


@login_required
def my_performances(request):
    try:
        athlete = request.user.athlete_profile
    except AthleteProfile.DoesNotExist:
        return redirect('complete_profile')

    performances = Performance.objects.filter(
        athlete=athlete
    ).order_by('-competition_date')

    return render(request,'core/my_performances.html',
        {
            'performances': performances,
            'athlete': athlete,
        }
    )


def calculate_event_rankings(event, gender=None):

    # Get athletes with approved performances in this event 
    athletes = AthleteProfile.objects.filter(
        performances__event=event,
        performances__verification__status='APPROVED'
    ) 

    # Filter athletes by gender when selected
    if gender:
        athletes = athletes.filter(
            gender=gender
        )

    athletes = athletes.distinct()

    rankings = []

    for athlete in athletes:

        performances = Performance.objects.filter(
            athlete=athlete,
            event=event,
            verification__status='APPROVED'
        )

        # Apply gender filter to the ranking data as well
        if gender and athlete.gender != gender:
            continue

        if performances.exists():

            total = sum(
                performance.result
                for performance in performances
            )
            average = total / performances.count()
            rankings.append({
                'athlete': athlete,
                'average': average,
                'best': min(
                    performance.result
                    for performance in performances
                ),

                'races': performances.count(),
            })

    # For athletics, lower time is better
    rankings.sort(
        key=lambda x: x['average']
    )

    # Assign ranking positions
    for position, ranking in enumerate(
        rankings,
        start=1
    ):

        ranking['position'] = position

    return rankings


def get_athlete_ranking(athlete, event):
    rankings = calculate_event_rankings(event)

    for ranking in rankings:
        if ranking['athlete'].id == athlete.id:
            return ranking

    return None


def rankings(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    rankings = calculate_event_rankings(event)

    return render(
        request,
        'core/rankings.html',
        {
            'event': event,
            'rankings': rankings,
        }
    )

def index(request):
    return render(request, 'core/index.html')


def talent_discovery(request):
    """
    Renders the talent discovery leaderboard with filtering by athlete name,
    gender, event, county, and sorting order.
    """
    # 1. Extract and sanitize request GET parameters
    search_query = request.GET.get('search', '').strip()
    gender = request.GET.get('gender', '').strip().lower()
    event_id = request.GET.get('event', '').strip()
    county = request.GET.get('county', '').strip()
    sort_order = request.GET.get('sort', '').strip()

    # 2. Get choices for filter dropdowns
    events = Event.objects.all()[:15]  # Limit to first 15 events

    # Retrieve unique counties, excluding empty or null values
    counties = (
        AthleteProfile.objects.filter(
            performances__verification__status='APPROVED'
        )
        .exclude(county__isnull=True)
        .exclude(county='')
        .values_list('county', flat=True)
        .distinct()
        .order_by('county')
    )

    talent_by_event = []

    # 3. Process rankings per event
    for event in events:
        # Skip events that don't match selected event filter
        if event_id and str(event.id) != event_id:
            continue

        rankings = calculate_event_rankings(event)
        filtered_rankings = []

        for ranking in rankings:
            athlete = ranking.get('athlete')
            if not athlete:
                continue

            # Filter by search term (name, username, or string representation)
            if search_query:
                search_term = search_query.lower()
                user = getattr(athlete, 'user', None)
                full_name = user.get_full_name().lower() if user else ''
                username = user.username.lower() if user else ''
                athlete_str = str(athlete).lower()

                if (
                    search_term not in full_name
                    and search_term not in username
                    and search_term not in athlete_str
                ):
                    continue

            # Filter by county
            if county and getattr(athlete, 'county', '') != county:
                continue

            # Filter by gender (case-insensitive)
            if gender:
                athlete_gender = str(getattr(athlete, 'gender', '')).strip().lower()
                if athlete_gender != gender:
                    continue

            filtered_rankings.append(ranking)

        # Sort filtered rankings based on user selection
        if sort_order == 'worst':
            filtered_rankings.sort(
                key=lambda r: r.get('average', 0), reverse=True
            )
        else:
            filtered_rankings.sort(
                key=lambda r: r.get('average', 0)
            )

        # Recalculate positions after filtering
        for position, ranking in enumerate(filtered_rankings, start=1):
            ranking['position'] = position

        # Append event group if any athletes matched
        if filtered_rankings:
            talent_by_event.append({
                'event': event,
                'rankings': filtered_rankings,
            })

    # 4. Context variables matching the template requirements
    context = {
        'talent_by_event': talent_by_event,
        'events': events,
        'counties': counties,
        'search_query': search_query,
        'gender': gender,
        'selected_event': event_id,
        'selected_county': county,
        'sort_order': sort_order,
    }

    return render(request, 'core/talent_discovery.html', context)

def athlete_detail(request, athlete_id):
    athlete = get_object_or_404(AthleteProfile, id=athlete_id)
    # Get verified performances
    verified_performances = (
        Performance.objects.filter(
            athlete=athlete,
            verification__status='APPROVED'
        )
        .select_related('event')
        .order_by('competition_date')[:15] # Limit to the latest 15 performances
    )

    # Calculate the athletes age from their date of birth
    def calculate_age(born):
        from datetime import date
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    age = calculate_age(athlete.date_of_birth) if athlete.date_of_birth else None

    # Get events with verified performances
    events = Event.objects.filter(performances__in=verified_performances).distinct()

    # Existing event statistics
    event_statistics = []

    for event in events:
        average = athlete.get_event_average(event)
        best = athlete.get_event_best_result(event)
        verified_races = athlete.get_verified_race_count(event)

        if average is not None:
            event_statistics.append({
                'event': event,
                'average': average,
                'best': best,
                'verified_races': verified_races,
            })

    # Prepare performance data for the line graph
    performance_data = []

    for performance in verified_performances:
        performance_data.append({
            'event': performance.event.name,
            'result': float(performance.result),
            'date': performance.competition_date.strftime('%Y-%m-%d'),
            'competition': performance.competition_name,
        })

    context = {
        'athlete': athlete,
        'event_statistics': event_statistics,
        'performance_data': performance_data,
        'age': age,
    }

    return render(request, 'core/athlete_detail.html',context)
