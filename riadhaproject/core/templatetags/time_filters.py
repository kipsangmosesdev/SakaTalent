from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django import template

register = template.Library()


@register.filter
def format_seconds(value):
    """Format stored total seconds as a readable race duration."""
    try:
        total_centiseconds = int(
            (Decimal(str(value)) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        )
    except (InvalidOperation, TypeError, ValueError):
        return value

    if total_centiseconds < 0:
        return value

    hours, remainder = divmod(total_centiseconds, 360000)
    minutes, remainder = divmod(remainder, 6000)
    seconds, centiseconds = divmod(remainder, 100)

    if hours:
        return f'{hours}h {minutes:02d}m {seconds:02d}.{centiseconds:02d}s'
    if minutes:
        return f'{minutes}m {seconds:02d}.{centiseconds:02d}s'
    return f'{seconds}.{centiseconds:02d}s'
