def days_hours_minutes(td):
    return td.days, td.seconds // 3600, (td.seconds // 60) % 60
