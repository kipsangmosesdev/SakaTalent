"""General event-family training guidance for the athlete training workspace."""

import re


GUIDANCE = {
    'short_sprint': {
        'title': '100m / 200m sprint focus',
        'focus': 'Common training themes include block starts, acceleration, maximum speed, sprint technique, strength and speed endurance.',
        'examples': 'Log short starts and acceleration runs, faster relaxed repetitions, technique drills, or speed-endurance sessions. Repetitions can be shorter or longer than the race distance.',
        'source_label': 'World Athletics: 100m training',
        'source_url': 'https://worldathletics.org/disciplines/jumps/100-metres',
    },
    '400m': {
        'title': '400m sprint focus',
        'focus': '400m preparation combines speed, speed endurance, pacing, running technique and strength work.',
        'examples': 'Log acceleration or top-speed work, shorter or broken race-pace repetitions, speed-endurance sessions, and recovery sessions. A full 400m effort is a benchmark, not a requirement for every workout.',
        'source_label': 'World Athletics: 400m training',
        'source_url': 'https://worldathletics.org/disciplines/sprints/400-metres',
    },
    'middle_distance': {
        'title': '800m / 1500m middle-distance focus',
        'focus': 'Middle-distance preparation balances aerobic endurance, event-pace intervals, speed, efficient technique and recovery.',
        'examples': 'Log intervals of varied lengths, relaxed strides or speed work, steady runs, strength work, and easy recovery sessions. Repetition length and pace vary with the event and athlete.',
        'source_label': 'World Athletics: 1500m preparation',
        'source_url': 'https://worldathletics.org/disciplines/middle-distance/1500-metres',
    },
    'distance': {
        'title': 'Distance-running focus',
        'focus': 'Distance preparation commonly combines easy aerobic running, tempo or threshold work, longer intervals, short speed work and recovery.',
        'examples': 'Log easy or long runs, tempo sessions, intervals at varied distances, hills, strides, and recovery sessions. Longer races are not repeated at full distance in every workout.',
        'source_label': 'World Athletics: interval training by event',
        'source_url': 'https://worldathletics.org/personal-best/performance/speed-training-endurance-runners-benefits-limits',
    },
    'hurdles': {
        'title': 'Hurdles / steeplechase focus',
        'focus': 'Hurdle events combine sprint or distance fitness with event-specific clearance technique, rhythm and safe obstacle practice.',
        'examples': 'Log coach-led mobility and lead/trail-leg drills, hurdle rhythm or approach work, sprint intervals, and recovery. Practise obstacle technique with suitable equipment and coaching.',
        'source_label': 'World Athletics: sprint-hurdle development',
        'source_url': 'https://worldathletics.org/download/downloadnsa?filename=ce56cb33-866c-49c1-9c17-85caeea079f7.pdf&urlslug=development-of-young-sprint-hurdlers',
    },
    'relay': {
        'title': 'Relay focus',
        'focus': 'Relay preparation combines the relevant sprint training with acceleration, exchange-zone timing and baton handoffs.',
        'examples': 'Log acceleration and speed work, exchange-zone repetitions, baton handoffs, and recovery sessions. Use the team’s planned exchange distances and coach instructions.',
    },
    'general': {
        'title': 'Event-specific training focus',
        'focus': 'Training should develop the technique, physical qualities and recovery needs of the selected event.',
        'examples': 'Log the session type and what you did, such as drills, intervals, strength work or recovery. Follow a qualified coach’s plan for event-specific loading.',
    },
}


def get_event_training_guidance(event_name):
    """Return broad, non-prescriptive guidance based on an event name."""
    name = re.sub(r'\s+', ' ', str(event_name or '').casefold()).strip()
    if 'relay' in name or '4x' in name or '4 x' in name:
        key = 'relay'
    elif any(term in name for term in ('hurdle', 'steeple', 'barrier')):
        key = 'hurdles'
    elif re.search(r'(?<!\d)400\s*(?:m|metres?|meters?)?(?!\d)', name):
        key = '400m'
    elif re.search(r'(?<!\d)(?:60|80|100|200)\s*(?:m|metres?|meters?)(?!\w)', name):
        key = 'short_sprint'
    elif re.search(r'(?<!\d)(?:800|1500|1600|3000)\s*(?:m|metres?|meters?)(?!\w)', name) or 'mile' in name:
        key = 'middle_distance'
    elif re.search(r'(?<!\d)(?:5000|10000)\s*(?:m|metres?|meters?)(?!\w)', name) or any(term in name for term in ('5k', '10k', 'marathon', 'cross country')):
        key = 'distance'
    else:
        key = 'general'
    return {**GUIDANCE[key], 'reminder': 'These are common training themes, not a personalized schedule. Your coach should adapt sessions, intensity and recovery to your experience and circumstances.'}
