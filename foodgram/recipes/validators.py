from django.utils import timezone


def year_validator(value):
    current_year = timezone.now().year
    if value > current_year:
        raise ValueError(
            f'Значение года не может превышать текущий {current_year}')
