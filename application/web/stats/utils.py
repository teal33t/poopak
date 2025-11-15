from datetime import timedelta
from typing import Tuple


def days_hours_minutes(td: timedelta) -> Tuple[int, int, int]:
    return td.days, td.seconds // 3600, (td.seconds // 60) % 60
