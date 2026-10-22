from django.contrib import messages
import json
import logging
import secrets
import urllib.parse
import urllib.request
import re
from datetime import date
from difflib import get_close_matches

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from datetime import timedelta
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils import timezone
from core.models import AthleteProfile, Event, Performance, Verification, TrainingPlan, TrainingTarget
from .forms import SignUpForm, AthleteProfileForm, PerformanceForm, TrainingPlanForm, TrainingTargetForm, TrainingResultForm

logger = logging.getLogger(__name__)

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
    return _start_google_auth(request, 'signup')


def google_login(request):
    """Start Google OpenID Connect login using the shared callback."""
    return _start_google_auth(request, 'login')


def _start_google_auth(request, source):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        messages.error(request, 'Google sign-in is not configured yet.')
        return redirect('login' if source == 'login' else 'signup')

    state = secrets.token_urlsafe(32)
    request.session['google_signup_state'] = state
    request.session['google_auth_source'] = source
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
    source = request.session.pop('google_auth_source', 'signup')
    return_to = 'login' if source == 'login' else 'signup'
    if request.user.is_authenticated:
        return redirect('dashboard')
    expected_state = request.session.pop('google_signup_state', None)
    if not expected_state or not secrets.compare_digest(
        expected_state, request.GET.get('state', '')
    ):
        messages.error(request, 'Google signup could not be verified. Please try again.')
        return redirect(return_to)
    if request.GET.get('error') or not request.GET.get('code'):
        messages.error(request, 'Google sign-in was cancelled or could not be completed.')
        return redirect(return_to)

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        messages.error(request, 'Google sign-in is not configured yet.')
        return redirect(return_to)

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
                or not identity.get('sub')
                or not identity.get('email')):
            raise ValueError('Google identity did not pass validation')
    except Exception:
        messages.error(request, 'We could not verify your Google account. Please try again.')
        return redirect(return_to)

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
    """Return the exact public callback configured for the OAuth client."""
    if settings.GOOGLE_REDIRECT_URI:
        return settings.GOOGLE_REDIRECT_URI

    production_host = os.environ.get('VERCEL_PROJECT_PRODUCTION_URL', '').strip()
    if production_host:
        production_host = production_host.removeprefix('https://').strip('/')
        return f'https://{production_host}{reverse("google_signup_callback")}'

    return request.build_absolute_uri(reverse('google_signup_callback'))

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
def training_dashboard(request):
    try:
        athlete = request.user.athlete_profile
    except AthleteProfile.DoesNotExist:
        return redirect('complete_profile')

    today = timezone.localdate()
    plan, _ = TrainingPlan.objects.get_or_create(
        athlete=athlete,
        defaults={'championship_date': today + timedelta(days=30)},
    )

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_target':
            target_form = TrainingTargetForm(request.POST, plan=plan)
            if target_form.is_valid():
                target = target_form.save(commit=False)
                target.plan = plan
                target.save()
                messages.success(request, f'Training target added for {target.event.name}.')
                return redirect('training_dashboard')
            result_forms = {}
        elif action == 'add_result':
            target = get_object_or_404(
                TrainingTarget,
                pk=request.POST.get('target_id'),
                plan=plan,
            )
            result_form = TrainingResultForm(request.POST, target=target)
            if result_form.is_valid():
                training_result = result_form.save(commit=False)
                training_result.target = target
                training_result.save()
                messages.success(request, 'Training result saved to your private training log.')
                return redirect('training_dashboard')
            target_form = TrainingTargetForm(plan=plan)
            result_forms = {target.pk: result_form}
        else:
            return redirect('training_dashboard')
    else:
        target_form = TrainingTargetForm(plan=plan)
        result_forms = {}

    targets = list(
        plan.targets.select_related('event')
        .prefetch_related('training_results')
        .order_by('-created_at', '-pk')
    )
    for target in targets:
        results = list(target.training_results.all())
        target.latest_result = results[0] if results else None
        target.best_result = min(results, key=lambda result: result.result) if results else None
        target.training_count = len(results)
        target.days_until_championship = (target.competition_date - today).days
        if target.best_result:
            target.time_gap = abs(target.target_result - target.best_result.result)
        if target.pk not in result_forms:
            result_forms[target.pk] = TrainingResultForm(target=target)

    return render(request, 'core/training_dashboard.html', {
        'athlete': athlete,
        'plan': plan,
        'target_form': target_form,
        'targets': targets,
        'result_forms': result_forms,
        'today': today,
    })


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
    # Personal standings should compare athletes within the same gender category.
    rankings = calculate_event_rankings(event, gender=athlete.gender)

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


def scout_agent(request):
    """A lightweight scouting assistant grounded in verified race results."""
    return render(request, 'core/scout_agent.html')


def scout_agent_ask(request):
    """Generate Scout answers with OpenAI, grounded in verified results and backed by local logic."""
    from django.http import JsonResponse

    if request.method != 'POST':
        return JsonResponse({'error': 'Please send a question.'}, status=405)
    try:
        question = json.loads(request.body).get('question', '').strip()
    except (ValueError, AttributeError):
        question = ''
    if not question or len(question) > 500:
        return JsonResponse({'error': 'Enter a question of up to 500 characters.'}, status=400)

    # Handle greeting-only messages before the default ranking path. Otherwise
    # an unfiltered message such as "hello" is treated as a request for top athletes.
    normalized = question.casefold().strip()
    greeting_only = re.fullmatch(
        r"[\W_]*(?:hi|hello|hey|howdy|good\s+(?:morning|afternoon|evening))"
        r"[\W_]*(?:there|scout|saka)?[\W_]*",
        normalized,
    )
    if greeting_only:
        greeting = (
            'Hi! I’m Scout AI. I can help you find athletes by county or event, compare verified performances, or review an athlete’s results. What would you like to explore?'
        )
        return scout_openai_answer_or_fallback(question, greeting)

    records = Performance.objects.filter(
        verification__status='APPROVED'
    ).select_related('athlete__user', 'event').order_by('result', '-competition_date')
    if not records.exists():
        answer = 'There are no verified race results to explore yet. Check back when athlete performances have been approved.'
        return scout_openai_answer_or_fallback(question, answer)

    county_choices = list(AthleteProfile.COUNTY_CHOICES)
    county_match = next((
        (code, label) for code, label in AthleteProfile.COUNTY_CHOICES
        if re.search(r'(?<!\w)' + re.escape(label.casefold()) + r'(?!\w)', normalized)
        or re.search(r'(?<!\w)' + re.escape(code.casefold()) + r'(?!\w)', normalized)
    ), None)
    if not county_match:
        county_words = re.findall(r'[a-z]+', normalized)
        county_names = {re.sub(r'[^a-z]', '', label.casefold()): (code, label)
                        for code, label in county_choices}
        for word in county_words:
            closest = get_close_matches(word, county_names, n=1, cutoff=0.78)
            if closest:
                county_match = county_names[closest[0]]
                break
    gender_match = None
    if re.search(r'\b(ladies|women|woman|female|girls?)\b', normalized):
        gender_match = 'F'
    elif re.search(r'\b(men|man|male|boys?)\b', normalized):
        gender_match = 'M'
    age_match = re.search(r'\b(?:under|below|younger than|less than)\s+(\d{1,2})\b', normalized)
    age_limit = int(age_match.group(1)) if age_match else None
    compact_question = re.sub(r'[^a-z0-9]', '', normalized)
    event_match = next((event for event in Event.objects.all()
                        if re.sub(r'[^a-z0-9]', '', event.name.casefold()) in compact_question), None)
    race_terms = ('race', 'competition', 'meet', 'championship', 'at ')
    race_query = None
    for record in records:
        name = record.competition_name.strip()
        if len(name) > 2 and name.casefold() in normalized:
            race_query = name
            break

    scoped = records
    if event_match:
        scoped = scoped.filter(event=event_match)
    if county_match:
        scoped = scoped.filter(athlete__county=county_match[0])
    if gender_match:
        scoped = scoped.filter(athlete__gender=gender_match)
    if age_limit is not None:
        today = timezone.localdate()
        try:
            age_cutoff = today.replace(year=today.year - age_limit)
        except ValueError:  # Handle 29 February when the target year is not a leap year.
            age_cutoff = today.replace(year=today.year - age_limit, day=28)
        scoped = scoped.filter(athlete__date_of_birth__gt=age_cutoff)
    if race_query:
        scoped = scoped.filter(competition_name__iexact=race_query)

    athlete_profiles = AthleteProfile.objects.select_related('user')
    athlete_match = next((athlete for athlete in athlete_profiles
                          if str(athlete).casefold() in normalized), None)
    previous_athlete_ids = request.session.get('scout_agent_athlete_ids', [])
    refers_to_previous = bool(re.search(
        r'\b(she|her|he|him|his|they|them|their|that athlete|this athlete|that runner|this runner)\b',
        normalized,
    ))
    if not athlete_match and refers_to_previous and previous_athlete_ids:
        ordinal_match = re.search(r'\b(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)\b', normalized)
        ordinal_positions = {
            'first': 0, '1st': 0, 'second': 1, '2nd': 1, 'third': 2, '3rd': 2,
            'fourth': 3, '4th': 3, 'fifth': 4, '5th': 4,
        }
        if ordinal_match:
            position = ordinal_positions[ordinal_match.group(1)]
            athlete_id = previous_athlete_ids[position] if position < len(previous_athlete_ids) else None
            athlete_match = AthleteProfile.objects.filter(pk=athlete_id).select_related('user').first()
        elif len(previous_athlete_ids) == 1:
            athlete_match = AthleteProfile.objects.filter(
                pk=previous_athlete_ids[0]
            ).select_related('user').first()
        elif len(previous_athlete_ids) > 1:
            previous_athletes = AthleteProfile.objects.filter(
                pk__in=previous_athlete_ids
            ).select_related('user')
            names = ', '.join(str(athlete) for athlete in previous_athletes[:8])
            answer = f'Which athlete do you mean? The last results included {names}. Ask about one by name.'
            return scout_openai_answer_or_fallback(question, answer)
    if athlete_match:
        scoped = scoped.filter(athlete=athlete_match)

    county_presence_question = bool(county_match) and any(
        phrase in normalized for phrase in ('are there', 'any athletes', 'athletes from', 'athletes in', 'list athletes')
    ) and not event_match and not race_query and not athlete_match
    if county_presence_question:
        athletes = list(AthleteProfile.objects.filter(
            performances__verification__status='APPROVED',
            county=county_match[0],
        ))
        if gender_match:
            athletes = [athlete for athlete in athletes if athlete.gender == gender_match]
        if age_limit is not None:
            athletes = [athlete for athlete in athletes if athlete.date_of_birth > age_cutoff]
        athletes = sorted(set(athletes), key=lambda athlete: str(athlete).casefold())
        if athletes:
            names = ', '.join(str(athlete) for athlete in athletes[:12])
            qualifier = ('female ' if gender_match == 'F' else 'male ' if gender_match == 'M' else '')
            qualifier += f'under {age_limit} ' if age_limit is not None else ''
            answer = (f'Yes. I found {len(athletes)} verified {qualifier}athlete'
                      f'{"s" if len(athletes) != 1 else ""} from {county_match[1]}: {names}')
            if len(athletes) > 12:
                answer += f', and {len(athletes) - 12} more'
            answer += '. Ask for a specific event to compare their race times.'
        else:
            answer = f'I could not find verified performances for athletes from {county_match[1]}'
            if gender_match == 'F':
                answer += ' among female athletes'
            elif gender_match == 'M':
                answer += ' among male athletes'
            if age_limit is not None:
                answer += f' under {age_limit}'
            answer += '.'
        remember_scout_athletes(request, [athlete.pk for athlete in athletes])
        return scout_openai_answer_or_fallback(question, answer)

    age_list_question = age_limit is not None and 'athlet' in normalized and not any(
        term in normalized for term in ('top', 'fastest', 'best', 'rank')
    ) and not event_match and not athlete_match
    if age_list_question:
        athletes_by_id = {row.athlete_id: row.athlete for row in scoped}
        athletes = sorted(athletes_by_id.values(), key=lambda athlete: str(athlete).casefold())
        qualifier = f'under {age_limit}'
        if county_match:
            qualifier += f' in {county_match[1]}'
        if gender_match == 'F':
            qualifier += ' (female athletes)'
        elif gender_match == 'M':
            qualifier += ' (male athletes)'
        if athletes:
            names = ', '.join(
                f'{athlete} ({athlete.get_county_display()})' for athlete in athletes[:20]
            )
            answer = f'Found {len(athletes)} verified athletes {qualifier}: {names}'
            if len(athletes) > 20:
                answer += f', and {len(athletes) - 20} more'
            answer += '.'
        else:
            answer = f'I could not find verified athletes {qualifier}.'
        remember_scout_athletes(request, [athlete.pk for athlete in athletes])
        return scout_openai_answer_or_fallback(question, answer)

    context_athlete_ids = []
    if race_query or any(term in normalized for term in race_terms):
        if race_query:
            race_records = list(scoped.order_by('result')[:10])
            context_athlete_ids = [row.athlete_id for row in race_records]
            if not race_records:
                answer = f'I could not find verified results for {race_query}.'
            else:
                heading = f'At {race_query}'
                if event_match:
                    heading += f' ({event_match.name})'
                answer = heading + ', the verified results are: ' + '; '.join(
                    f'{i}. {row.athlete} — {row.event.name}, {format_agent_time(row.result)} '
                    f'({row.athlete.get_county_display()}, {row.competition_date:%d %b %Y})'
                    for i, row in enumerate(race_records, 1)
                ) + '.'
        elif event_match:
            race_records = list(scoped.order_by('competition_date', 'result')[:10])
            context_athlete_ids = [row.athlete_id for row in race_records]
            answer = (f'Here are verified {event_match.name} race entries'
                      f'{" in " + county_match[1] if county_match else ""}: ' + '; '.join(
                f'{row.athlete} — {row.competition_name}, {format_agent_time(row.result)} '
                f'({row.competition_date:%d %b %Y})' for row in race_records
            ) + '.') if race_records else 'No verified race results match those filters.'
        else:
            answer = 'For race results, ask with an event or competition name, for example “Show 5000m races in Nandi” or “Results at Nairobi City Marathon”.'
    else:
        # Aggregate each athlete's average and best verified time within the filters.
        groups = {}
        for row in scoped:
            group_key = (row.athlete_id, row.event_id)
            stats = groups.setdefault(group_key, {
                'athlete': row.athlete, 'event': row.event, 'times': [], 'latest': row.competition_date,
            })
            stats['times'].append(row.result)
        ranked = []
        for stats in groups.values():
            ranked.append({**stats, 'average': sum(stats['times']) / len(stats['times']), 'best': min(stats['times'])})
        ranked.sort(key=lambda item: (item['average'], -item['latest'].toordinal()))
        for item in ranked:
            if item['athlete'].pk not in context_athlete_ids:
                context_athlete_ids.append(item['athlete'].pk)
            if len(context_athlete_ids) == 5:
                break
        if not ranked:
            answer = 'No verified performances match those filters yet.'
        else:
            limit = 5
            label = f' in {county_match[1]}' if county_match else ''
            label += f' for {event_match.name}' if event_match else ''
            if gender_match == 'F':
                label = 'Female athletes' + label
            elif gender_match == 'M':
                label = 'Male athletes' + label
            if age_limit is not None:
                label += f' under {age_limit}'
            if athlete_match:
                label = f'{athlete_match} performance summary'
            answer = f'{label if athlete_match else "Top verified athletes" + label} (ranked by average time; lower is faster): ' + '; '.join(
                f'{i}. {item["athlete"]} — {item["event"].name}, '
                f'average {format_agent_time(item["average"])}, best {format_agent_time(item["best"])} '
                f'across {len(item["times"])} race{"s" if len(item["times"]) != 1 else ""}'
                for i, item in enumerate(ranked[:limit], 1)
            ) + '.'
            if not athlete_match and not event_match and not county_match:
                answer += ' Include a county or event name to narrow the search.'

    remember_scout_athletes(request, context_athlete_ids)
    return scout_openai_answer_or_fallback(question, answer)


def scout_openai_answer_or_fallback(question, grounded_answer):
    """Ask OpenAI to phrase a response grounded in verified scouting data."""
    from django.http import JsonResponse
    from urllib.error import HTTPError, URLError

    api_key = getattr(settings, 'OPENAI_API_KEY', '').strip()
    if not api_key:
        logger.error('Scout OpenAI request skipped: OPENAI_API_KEY is not configured.')
        return JsonResponse({
            'error': 'Scout AI is not connected to OpenAI yet. Configure OPENAI_API_KEY on the server.'
        }, status=503)

    payload = {
        'model': getattr(settings, 'OPENAI_MODEL', 'gpt-6-astra'),
        'instructions': (
            'respond to any greetings before proceeding with the user’s question. '
            'You are Scout AI, SakaTalent’s athletics scouting assistant. Answer the user’s '
            'question using only the verified-data result supplied below. Never invent athlete '
            'facts, results, rankings, or explanations. If the supplied result does not answer '
            'the question, say what verified information is available and ask one useful '
            'follow-up. Explain that lower times are faster when relevant. Keep the answer '
            'concise and conversational; do not repeat the question.'
        ),
        'input': json.dumps({
            'user_question': question,
            'verified_data_result': grounded_answer,
        }),
        'max_output_tokens': 220,
    }
    request_data = urllib.request.Request(
        'https://api.openai.com/v1/responses',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(request_data, timeout=12) as response:
            result = json.loads(response.read().decode('utf-8'))
        generated = ' '.join(
            part.get('text', '').strip()
            for item in result.get('output', [])
            if item.get('type') == 'message'
            for part in item.get('content', [])
            if part.get('type') == 'output_text' and part.get('text', '').strip()
        ).strip()
        if generated:
            return JsonResponse({'answer': generated[:1800]})
        logger.error('Scout OpenAI request returned no text (model=%s).', payload['model'])
        return JsonResponse({
            'error': 'OpenAI returned an empty response. Check the server logs and model configuration.'
        }, status=502)
    except HTTPError as exc:
        detail = exc.read().decode('utf-8', errors='replace')[:1000]
        logger.error('Scout OpenAI API returned HTTP %s (model=%s): %s', exc.code, payload['model'], detail)
        return JsonResponse({
            'error': f'OpenAI request failed (HTTP {exc.code}). Check OPENAI_API_KEY, billing, model access, and server logs.'
        }, status=502)
    except (URLError, TimeoutError, ValueError, KeyError, TypeError) as exc:
        logger.exception('Scout OpenAI request failed (model=%s): %s', payload['model'], exc)
        return JsonResponse({
            'error': 'Scout could not get a response from OpenAI. Check the server logs and try again.'
        }, status=502)


def remember_scout_athletes(request, athlete_ids):
    """Keep the latest answer's athlete references for short chat follow-ups."""
    request.session['scout_agent_athlete_ids'] = list(dict.fromkeys(athlete_ids))[:20]


def format_agent_time(seconds):
    """Format stored race seconds as a readable race time."""
    total = int(float(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    hundredths = int(round((float(seconds) - total) * 100))
    if hundredths == 100:
        secs += 1
        hundredths = 0
    return (f'{hours}:{minutes:02d}:{secs:02d}' if hours else f'{minutes}:{secs:02d}') + f'.{hundredths:02d}'


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
            is_verified=True,
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
            if not athlete or not athlete.is_verified:
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
