from datetime import datetime, timedelta
from dateutil import parser
import json

from vacation_tracker.utils.db import get_db
from vacation_tracker.utils.date_utils import get_date_range_days, get_continuous_vacation_days
from vacation_tracker.services.holiday_service import get_holiday_name, get_cached_holidays

# Constants
TOTAL_VACATION_DAYS = 14

def get_all_vacation_days():
    """Get all vacation days from the database."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM vacation_days ORDER BY start_date')
    vacation_days_raw = cursor.fetchall()
    
    # Get holiday dates for continuous period calculation
    holidays = get_cached_holidays()
    holiday_dates = [holiday['date'] for holiday in holidays]
    
    # Convert to a list of dictionaries for easy template access
    vacation_days = []
    total_used_days = 0
    
    for row in vacation_days_raw:
        vacation_day = dict(row)
        # Convert date strings to date objects for formatting in template
        vacation_day['start_date'] = datetime.strptime(vacation_day['start_date'], '%Y-%m-%d').date()
        vacation_day['end_date'] = datetime.strptime(vacation_day['end_date'], '%Y-%m-%d').date()
        vacation_day['days'] = get_date_range_days(vacation_day['start_date'], vacation_day['end_date'])
        total_used_days += vacation_day['days']
        
        # Calculate continuous vacation period (including weekends and holidays)
        continuous_period = get_continuous_vacation_days(
            vacation_day['start_date'], 
            vacation_day['end_date'],
            holiday_dates
        )
        
        vacation_day['continuous_start'] = continuous_period['continuous_start']
        vacation_day['continuous_end'] = continuous_period['continuous_end']
        vacation_day['continuous_days'] = continuous_period['total_days']
        vacation_day['is_long_weekend'] = continuous_period['is_long_weekend']
        vacation_day['includes_weekends'] = len(continuous_period['weekends']) > 0
        vacation_day['adjacent_holidays'] = []
        
        # Process adjacent holidays for UI display
        for holiday_date in continuous_period['adjacent_holidays']:
            holiday_name = get_holiday_name(holiday_date)
            if holiday_name:
                vacation_day['adjacent_holidays'].append({
                    'date': holiday_date,
                    'name': holiday_name
                })
        
        vacation_days.append(vacation_day)
    
    remaining_days = TOTAL_VACATION_DAYS - total_used_days
    
    return {
        'vacation_days': vacation_days,
        'total_used_days': total_used_days,
        'remaining_days': remaining_days
    }

def get_vacation_by_id(id):
    """Get a specific vacation entry by ID."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM vacation_days WHERE id = ?', (id,))
    return cursor.fetchone()

def add_vacation_days(selected_dates_json, note):
    """Add vacation days to the database."""
    error = None
    
    try:
        # Parse the selected dates from JSON
        selected_dates = json.loads(selected_dates_json)
        
        if not selected_dates:
            return False, "Please select at least one date"
        
        # Convert dates to datetime.date objects
        dates = [parser.parse(date_str).date() for date_str in selected_dates]
        start_date = min(dates)
        end_date = max(dates)
        
        # Check if any of the selected dates are in the past
        today = datetime.now().date()
        if start_date < today:
            return False, "Cannot add vacation days in the past"
        
        # Check for holidays in the selected range
        holiday_conflicts = []
        current_date = start_date
        while current_date <= end_date:
            holiday_name = get_holiday_name(current_date)
            if holiday_name:
                holiday_conflicts.append(f"{current_date.strftime('%B %d, %Y')} ({holiday_name}) - Bank Holiday")
            current_date += timedelta(days=1)
        
        if holiday_conflicts:
            conflict_message = "The following dates are bank holidays and can't be booked: " + ", ".join(holiday_conflicts)
            return False, conflict_message
        
        # Check if any dates in the range are already booked
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT start_date, end_date 
            FROM vacation_days 
            WHERE (start_date <= ? AND end_date >= ?) 
               OR (start_date <= ? AND end_date >= ?)
        ''', (end_date.isoformat(), start_date.isoformat(), 
              end_date.isoformat(), end_date.isoformat()))
        
        existing_ranges = cursor.fetchall()
        if existing_ranges:
            existing_dates = []
            for range_row in existing_ranges:
                range_start = datetime.strptime(range_row['start_date'], '%Y-%m-%d').date()
                range_end = datetime.strptime(range_row['end_date'], '%Y-%m-%d').date()
                existing_dates.append(f"{range_start.strftime('%Y-%m-%d')} to {range_end.strftime('%Y-%m-%d')}")
            
            return False, f'The following date ranges are already booked: {", ".join(existing_dates)}'
        
        # Calculate total days in the range
        days_in_range = get_date_range_days(start_date, end_date)
        
        # Check if adding this range would exceed the total vacation days
        cursor.execute('''
            SELECT SUM((julianday(end_date) - julianday(start_date) + 1)) as total_days
            FROM vacation_days
        ''')
        current_total = cursor.fetchone()['total_days'] or 0
        
        if current_total + days_in_range > TOTAL_VACATION_DAYS:
            return False, f'Adding {days_in_range} days would exceed your total vacation days'
        
        # Add the date range
        cursor.execute(
            'INSERT INTO vacation_days (start_date, end_date, note, created_at) VALUES (?, ?, ?, ?)',
            (start_date.isoformat(), end_date.isoformat(), note, datetime.now().isoformat())
        )
        db.commit()
        
        success_message = f'Successfully booked {days_in_range} vacation days from {start_date.strftime("%B %d")} to {end_date.strftime("%B %d")}!'
        return True, success_message
            
    except (ValueError, json.JSONDecodeError):
        return False, 'Invalid date format'
    
    return False, 'Unknown error occurred'

def delete_vacation_days(id):
    """Delete vacation days by ID."""
    db = get_db()
    cursor = db.cursor()
    
    # Check if vacation range exists
    cursor.execute('SELECT * FROM vacation_days WHERE id = ?', (id,))
    vacation_range = cursor.fetchone()
    if not vacation_range:
        return False, 'Vacation range not found'
    
    # Delete the vacation range
    cursor.execute('DELETE FROM vacation_days WHERE id = ?', (id,))
    db.commit()
    
    # Format dates for the success message
    start_date = datetime.strptime(vacation_range['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(vacation_range['end_date'], '%Y-%m-%d').date()
    days = get_date_range_days(start_date, end_date)
    
    success_message = f'Successfully deleted {days} vacation days from {start_date.strftime("%B %d")} to {end_date.strftime("%B %d")}!'
    return True, success_message

def edit_vacation_days(id, selected_dates_json, note):
    """Edit vacation days by ID."""
    from datetime import timedelta
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Check if vacation range exists
        cursor.execute('SELECT * FROM vacation_days WHERE id = ?', (id,))
        vacation_range = cursor.fetchone()
        if not vacation_range:
            return False, 'Vacation range not found'
        
        # Parse the selected dates from JSON
        selected_dates = json.loads(selected_dates_json)
        
        if not selected_dates:
            return False, 'Please select at least one date'
        
        # Convert dates to datetime.date objects
        dates = [parser.parse(date_str).date() for date_str in selected_dates]
        start_date = min(dates)
        end_date = max(dates)
        
        # Check if any of the selected dates are in the past
        today = datetime.now().date()
        if start_date < today:
            return False, 'Cannot add vacation days in the past'
        
        # Check for holidays in the selected range
        holiday_conflicts = []
        current_date = start_date
        while current_date <= end_date:
            holiday_name = get_holiday_name(current_date)
            if holiday_name:
                holiday_conflicts.append(f"{current_date.strftime('%B %d, %Y')} ({holiday_name}) - Bank Holiday")
            current_date += timedelta(days=1)
        
        if holiday_conflicts:
            conflict_message = "The following dates are bank holidays and can't be booked: " + ", ".join(holiday_conflicts)
            return False, conflict_message
        
        # Check if any dates in the range are already booked (excluding the current range)
        cursor.execute('''
            SELECT start_date, end_date 
            FROM vacation_days 
            WHERE id != ? AND (
                (start_date <= ? AND end_date >= ?) 
                OR (start_date <= ? AND end_date >= ?)
            )
        ''', (id, end_date.isoformat(), start_date.isoformat(), 
              end_date.isoformat(), end_date.isoformat()))
        
        existing_ranges = cursor.fetchall()
        if existing_ranges:
            existing_dates = []
            for range_row in existing_ranges:
                range_start = datetime.strptime(range_row['start_date'], '%Y-%m-%d').date()
                range_end = datetime.strptime(range_row['end_date'], '%Y-%m-%d').date()
                existing_dates.append(f"{range_start.strftime('%Y-%m-%d')} to {range_end.strftime('%Y-%m-%d')}")
            
            return False, f'The following date ranges are already booked: {", ".join(existing_dates)}'
        
        # Calculate total days in the range
        days_in_range = get_date_range_days(start_date, end_date)
        
        # Get current days used by this entry
        old_start_date = datetime.strptime(vacation_range['start_date'], '%Y-%m-%d').date()
        old_end_date = datetime.strptime(vacation_range['end_date'], '%Y-%m-%d').date()
        old_days = get_date_range_days(old_start_date, old_end_date)
        
        # Calculate the difference in days
        net_day_change = days_in_range - old_days
        
        # Check if editing this range would exceed the total vacation days
        cursor.execute('''
            SELECT SUM((julianday(end_date) - julianday(start_date) + 1)) as total_days
            FROM vacation_days
            WHERE id != ?
        ''', (id,))
        current_total = cursor.fetchone()['total_days'] or 0
        
        if current_total + days_in_range > TOTAL_VACATION_DAYS:
            return False, f'Changing to {days_in_range} days would exceed your total vacation days'
        
        # Update the date range
        cursor.execute(
            'UPDATE vacation_days SET start_date = ?, end_date = ?, note = ? WHERE id = ?',
            (start_date.isoformat(), end_date.isoformat(), note, id)
        )
        db.commit()
        
        if net_day_change > 0:
            message = f'Successfully updated vacation: added {abs(net_day_change)} more days'
        elif net_day_change < 0:
            message = f'Successfully updated vacation: removed {abs(net_day_change)} days'
        else:
            message = 'Successfully updated vacation details'
            
        success_message = f'{message} for {start_date.strftime("%B %d")} to {end_date.strftime("%B %d")}!'
        return True, success_message
            
    except (ValueError, json.JSONDecodeError):
        return False, 'Invalid date format'
    
    return False, 'Unknown error occurred' 