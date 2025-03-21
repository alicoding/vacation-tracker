from flask import Blueprint, render_template, flash, redirect, url_for, request, g
import json
from datetime import datetime, timedelta

from vacation_tracker.services.vacation_service import (
    get_all_vacation_days, add_vacation_days, edit_vacation_days, delete_vacation_days, 
    TOTAL_VACATION_DAYS
)
from vacation_tracker.services.holiday_service import (
    get_cached_holidays, get_last_holiday_update, get_deduplicated_holidays
)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Get vacation days data
    vacation_data = get_all_vacation_days()
    vacation_days = vacation_data['vacation_days']
    remaining_days = vacation_data['remaining_days']
    
    # Get upcoming holidays - deduplicated
    upcoming_holidays = get_deduplicated_holidays()
    
    # Pass holidays to the template as a list of date strings for the date picker
    holiday_dates = [holiday['date'] for holiday in upcoming_holidays if holiday.get('is_bank_holiday', False)]
    ontario_holidays = [holiday['date'] for holiday in upcoming_holidays if holiday.get('is_ontario_holiday', False)]
    
    # Create a list of all booked vacation dates for highlighting in the calendar
    booked_dates = []
    for vacation in vacation_days:
        current_date = vacation['start_date']
        while current_date <= vacation['end_date']:
            booked_dates.append(current_date.isoformat())
            current_date += timedelta(days=1)
    
    # Format holidays for display in the UI - already deduplicated
    formatted_holidays = []
    for holiday in upcoming_holidays[:10]:  # Show the next 10 holidays
        # Convert string date to date object
        if isinstance(holiday['date_obj'], str):
            holiday_date = datetime.strptime(holiday['date_obj'], '%Y-%m-%d').date()
        else:
            holiday_date = holiday['date_obj']
            
        # Get date in ISO format
        if 'date' in holiday:
            holiday_date_iso = holiday['date']
        else:
            holiday_date_iso = holiday_date.isoformat()
            
        # Check if the holiday overlaps with a vacation
        is_overlapping = holiday_date_iso in booked_dates
        
        # Enhanced adjacency detection that accounts for weekends
        is_adjacent_to_vacation = False
        
        # 1. Check if day right before or after is booked
        day_before = (holiday_date - timedelta(days=1)).isoformat()
        day_after = (holiday_date + timedelta(days=1)).isoformat()
        
        is_day_before_booked = day_before in booked_dates
        is_day_after_booked = day_after in booked_dates
        
        # 2. Check for long weekend patterns
        weekday = holiday_date.weekday()  # 0=Monday, 6=Sunday
        
        # If holiday is on Monday, check if Friday before is booked
        if weekday == 0:  # Monday holiday
            friday_before = (holiday_date - timedelta(days=3)).isoformat()
            is_friday_before_booked = friday_before in booked_dates
            if is_friday_before_booked:
                is_adjacent_to_vacation = True
                
        # If holiday is on Friday, check if Monday after is booked
        elif weekday == 4:  # Friday holiday
            monday_after = (holiday_date + timedelta(days=3)).isoformat()
            is_monday_after_booked = monday_after in booked_dates
            if is_monday_after_booked:
                is_adjacent_to_vacation = True
        
        # If holiday is on Tuesday, check if Friday-Monday is booked
        elif weekday == 1:  # Tuesday holiday
            monday_before = (holiday_date - timedelta(days=1)).isoformat()
            friday_before = (holiday_date - timedelta(days=4)).isoformat()
            is_monday_before_booked = monday_before in booked_dates
            is_friday_before_booked = friday_before in booked_dates
            if is_friday_before_booked and is_monday_before_booked:
                is_adjacent_to_vacation = True
                
        # If holiday is on Thursday, check if Friday-Monday after is booked
        elif weekday == 3:  # Thursday holiday
            friday_after = (holiday_date + timedelta(days=1)).isoformat()
            monday_after = (holiday_date + timedelta(days=4)).isoformat()
            is_friday_after_booked = friday_after in booked_dates
            is_monday_after_booked = monday_after in booked_dates
            if is_friday_after_booked and is_monday_after_booked:
                is_adjacent_to_vacation = True
                
        # Finally, check the immediate days before/after if we haven't already matched
        if not is_adjacent_to_vacation:
            is_adjacent_to_vacation = is_day_before_booked or is_day_after_booked
            
        # Format the date for display
        formatted_date = holiday_date.strftime('%B %d, %Y')
        
        # Add the weekday name to make it clearer
        weekday_name = holiday_date.strftime('%A')
        formatted_date_with_weekday = f"{formatted_date} ({weekday_name})"
        
        formatted_holidays.append({
            'name': holiday.get('localName', holiday.get('name', '')),
            'date': formatted_date_with_weekday,
            'date_iso': holiday_date_iso,
            'weekday': weekday_name,
            'is_bank_holiday': holiday.get('is_bank_holiday', True),
            'is_ontario_holiday': holiday.get('is_ontario_holiday', False),
            'source': holiday.get('holiday_source', 'Canadian Bank Holiday'),
            'overlaps_vacation': is_overlapping,
            'is_adjacent_to_vacation': is_adjacent_to_vacation and not is_overlapping
        })
    
    # Calculate progress percentage for the progress bar
    progress_percentage = int((remaining_days / TOTAL_VACATION_DAYS) * 100)
    
    # Get the last update time for holidays
    last_update = get_last_holiday_update()
    
    return render_template('index.html', 
                         vacation_days=vacation_days,
                         remaining_days=remaining_days,
                         total_days=TOTAL_VACATION_DAYS,
                         progress_percentage=progress_percentage,
                         holidays=formatted_holidays,
                         holiday_dates_json=json.dumps(holiday_dates),
                         booked_dates_json=json.dumps(booked_dates),
                         ontario_holidays_json=json.dumps(ontario_holidays),
                         last_holiday_update=last_update)

@main_bp.route('/add', methods=['POST'])
def add_vacation():
    selected_dates_json = request.form.get('selected_dates', '[]')
    note = request.form.get('note', '')
    
    success, message = add_vacation_days(selected_dates_json, note)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('main.index'))

@main_bp.route('/delete/<int:id>')
def delete_vacation(id):
    success, message = delete_vacation_days(id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('main.index'))

@main_bp.route('/edit/<int:id>', methods=['POST'])
def edit_vacation(id):
    selected_dates_json = request.form.get('selected_dates', '[]')
    note = request.form.get('note', '')
    
    success, message = edit_vacation_days(id, selected_dates_json, note)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('main.index'))