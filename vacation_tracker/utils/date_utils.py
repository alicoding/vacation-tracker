from datetime import datetime, date, timedelta

def get_date_range_days(start_date, end_date):
    """Calculate the number of days in a date range (inclusive)."""
    return (end_date - start_date).days + 1

def parse_date(date_str):
    """Parse ISO format date string to date object."""
    return datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None

def is_weekend(date_obj):
    """Check if a date is a weekend (Saturday or Sunday)."""
    return date_obj.weekday() >= 5  # 5=Saturday, 6=Sunday

def get_continuous_vacation_days(start_date, end_date, holidays=None):
    """
    Calculate the continuous vacation period including weekends and holidays.
    Returns a dict with start_date, end_date, and info about any adjacent holidays or weekends.
    """
    continuous_start = start_date
    continuous_end = end_date
    weekends = []
    adjacent_holidays = []
    
    # Check if there are days before the start_date that are weekends or holidays
    day_before = start_date - timedelta(days=1)
    while is_weekend(day_before) or (holidays and day_before.isoformat() in holidays):
        if is_weekend(day_before):
            weekends.append(day_before)
        elif holidays and day_before.isoformat() in holidays:
            adjacent_holidays.append(day_before)
        continuous_start = day_before
        day_before = day_before - timedelta(days=1)
    
    # Check if there are days after the end_date that are weekends or holidays
    day_after = end_date + timedelta(days=1)
    while is_weekend(day_after) or (holidays and day_after.isoformat() in holidays):
        if is_weekend(day_after):
            weekends.append(day_after)
        elif holidays and day_after.isoformat() in holidays:
            adjacent_holidays.append(day_after)
        continuous_end = day_after
        day_after = day_after + timedelta(days=1)
    
    # Calculate total days in the continuous period
    total_days = get_date_range_days(continuous_start, continuous_end)
    
    return {
        'continuous_start': continuous_start,
        'continuous_end': continuous_end,
        'total_days': total_days,
        'weekends': weekends,
        'adjacent_holidays': adjacent_holidays,
        'is_long_weekend': len(weekends) > 0
    } 