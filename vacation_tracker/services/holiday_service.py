import json
import re
import traceback
from datetime import datetime, date, timedelta
import requests

from vacation_tracker.utils.db import get_db

# Bank API URL for validation (e.g., major Canadian bank websites that list their holidays)
BANK_VALIDATION_SOURCES = [
    "https://www.td.com/ca/en/personal-banking/help-centre/branch-holiday-hours",
    "https://www.rbcroyalbank.com/ways-to-bank/holiday-schedule.html",
    "https://www.cibc.com/en/about-cibc/contact-us/hours-and-locations.html"
]

def get_holidays_for_year(year):
    """Fetch Canadian public holidays from Nager.Date API for a given year and identify bank holidays."""
    url = f'https://date.nager.at/api/v3/PublicHolidays/{year}/CA'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        holidays = response.json()
        
        # Process holidays to identify which ones are bank holidays
        bank_holidays = identify_bank_holidays(holidays, year)
        return bank_holidays
    except Exception as e:
        print(f"Error fetching holidays: {e}")
        traceback.print_exc()
        return []

def identify_bank_holidays(holidays, year):
    """
    Identifies which holidays are observed by Canadian banks based on:
    1. Known patterns (statutory holidays + certain specific days)
    2. Getting holiday information from bank websites (when implemented)
    """
    bank_holidays = []
    ontario_holidays = []
    
    # Rules for Canadian bank holidays:
    # - All statutory federal holidays
    # - Boxing Day
    # - Provincial holidays where banks operate (e.g. Family Day)
    # - Not Easter Monday (which some online listings incorrectly include)
    
    for holiday in holidays:
        holiday_name = holiday['name'].lower()
        local_name = holiday.get('localName', '').lower()
        
        # Check if this is likely a bank holiday by name and type
        is_bank_holiday = False
        is_ontario_holiday = False
        
        # Federal statutory holidays (always bank holidays)
        if any(statutory in holiday_name for statutory in [
            'new year', 'canada day', 'labour day', 'christmas', 
            'thanksgiving', 'good friday', 'remembrance day',
            'national day for truth and reconciliation'
        ]):
            is_bank_holiday = True
        
        # Boxing Day is observed by banks in Canada
        elif 'boxing day' in holiday_name:
            is_bank_holiday = True
        
        # Family Day (February) - bank holiday in provinces that observe it
        elif 'family day' in holiday_name:
            is_bank_holiday = True
            is_ontario_holiday = True
        
        # Victoria Day (May) - bank holiday across Canada
        elif 'victoria day' in holiday_name:
            is_bank_holiday = True
            
        # Civic/Provincial holidays (August) - many banks observe these
        elif ('civic holiday' in holiday_name or 
              (holiday.get('date', '').startswith(f"{year}-08") and 
               any(term in holiday_name for term in ['provincial', 'civic', 'heritage']))):
            is_bank_holiday = True
            is_ontario_holiday = True
        
        # Explicitly exclude Easter Monday (not a bank holiday in Canada despite sometimes being listed)
        elif 'easter monday' in holiday_name:
            is_bank_holiday = False
            
        # Ontario-specific holidays that aren't bank holidays
        elif any(term in holiday_name for term in ['ontario', 'provincial', 'civic']):
            is_ontario_holiday = True
            
        # For any other holidays, default to not a bank holiday
        else:
            is_bank_holiday = False
            
        # If identified as a bank holiday or Ontario holiday, add to our list
        if is_bank_holiday:
            holiday['is_bank_holiday'] = True
            holiday['holiday_source'] = 'Identified using Canadian banking standards'
            bank_holidays.append(holiday)
            
        if is_ontario_holiday:
            holiday['is_ontario_holiday'] = True
            if not is_bank_holiday:
                holiday['holiday_source'] = 'Ontario Provincial Holiday'
                ontario_holidays.append(holiday)
    
    # Return both bank holidays and ontario-specific holidays
    return bank_holidays + ontario_holidays

def validate_bank_holidays(holidays):
    """
    For future implementation: Validate holidays against bank websites
    This function would scrape bank websites to confirm the holidays
    """
    # This would involve web scraping to validate against bank websites
    # For now, we rely on our identification rules
    return holidays

def refresh_holiday_cache():
    """Update the holiday cache with current and next year's holidays."""
    current_year = datetime.now().year
    years_to_fetch = [current_year, current_year + 1]
    
    db = get_db()
    cursor = db.cursor()
    cached_date = datetime.now().isoformat()
    
    # Clear existing holidays for the years we're about to update
    cursor.execute('DELETE FROM holidays WHERE strftime("%Y", date) IN (?, ?)', 
                  (str(current_year), str(current_year + 1)))
    
    total_holidays = 0
    for year in years_to_fetch:
        holidays = get_holidays_for_year(year)
        for holiday in holidays:
            # Add the holiday to the database with bank holiday flag
            cursor.execute(
                'INSERT INTO holidays (name, date, localName, country_code, cache_date, is_bank_holiday, holiday_source) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (holiday['name'], holiday['date'], holiday.get('localName', holiday['name']), 
                 holiday['countryCode'], cached_date, 
                 holiday.get('is_bank_holiday', False),
                 holiday.get('holiday_source', 'Canadian Holiday'))
            )
            
            # Check if we need to add the is_ontario_holiday column
            cursor.execute("PRAGMA table_info(holidays)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'is_ontario_holiday' not in columns:
                cursor.execute("ALTER TABLE holidays ADD COLUMN is_ontario_holiday BOOLEAN DEFAULT 0")
            
            # Update the ontario_holiday flag
            cursor.execute(
                'UPDATE holidays SET is_ontario_holiday = ? WHERE date = ?',
                (holiday.get('is_ontario_holiday', False), holiday['date'])
            )
            
            total_holidays += 1
    
    db.commit()
    return total_holidays > 0

def get_cached_holidays(force_refresh=False):
    """Get holidays from cache, refreshing if necessary."""
    db = get_db()
    cursor = db.cursor()
    
    # Check if we need to refresh the cache
    cursor.execute('SELECT MAX(cache_date) as last_update FROM holidays')
    result = cursor.fetchone()
    
    if force_refresh or not result or not result['last_update']:
        refresh_holiday_cache()
    else:
        # Check if cache is older than a month or if we're in December and 
        # haven't cached next year's holidays yet
        last_update = datetime.fromisoformat(result['last_update'])
        current_date = datetime.now()
        
        # If cache is older than a month or we're in December and need next year's data
        one_month_ago = current_date - timedelta(days=30)
        if (last_update < one_month_ago or 
            (current_date.month == 12 and current_date.year + 1 > last_update.year)):
            refresh_holiday_cache()
            
    # Check if the ontario_holiday column exists
    cursor.execute("PRAGMA table_info(holidays)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'is_ontario_holiday' not in columns:
        cursor.execute("ALTER TABLE holidays ADD COLUMN is_ontario_holiday BOOLEAN DEFAULT 0")
        db.commit()
    
    # Get all holidays from now until the end of next year
    cursor.execute('''
        SELECT name, date, localName, is_bank_holiday, is_ontario_holiday, holiday_source 
        FROM holidays 
        WHERE date >= ? 
        ORDER BY date
    ''', (datetime.now().date().isoformat(),))
    
    holidays = []
    for row in cursor.fetchall():
        holiday = dict(row)
        holiday['date_obj'] = datetime.strptime(holiday['date'], '%Y-%m-%d').date()
        holidays.append(holiday)
    
    return holidays

def get_deduplicated_holidays():
    """Get deduplicated holidays from the cache."""
    # Get holidays from the cache
    holidays = get_cached_holidays()
    
    # Deduplicate holidays by date
    unique_holidays = {}
    for holiday in holidays:
        date_str = holiday['date_obj'].strftime('%Y-%m-%d')
        # If we already have this date, only keep it if it's a bank holiday and the existing one isn't
        if date_str in unique_holidays:
            if holiday.get('is_bank_holiday', False) and not unique_holidays[date_str].get('is_bank_holiday', False):
                unique_holidays[date_str] = holiday
        else:
            unique_holidays[date_str] = holiday
    
    return list(unique_holidays.values())

def is_holiday(date_obj):
    """Check if a given date is a holiday."""
    db = get_db()
    cursor = db.cursor()
    
    date_str = date_obj.isoformat() if isinstance(date_obj, date) else date_obj
    
    cursor.execute('SELECT COUNT(*) as count FROM holidays WHERE date = ?', (date_str,))
    result = cursor.fetchone()
    return result['count'] > 0

def get_holiday_name(date_obj):
    """Get the name of a holiday for a given date, or None if it's not a holiday."""
    db = get_db()
    cursor = db.cursor()
    
    date_str = date_obj.isoformat() if isinstance(date_obj, date) else date_obj
    
    cursor.execute('SELECT localName FROM holidays WHERE date = ?', (date_str,))
    result = cursor.fetchone()
    return result['localName'] if result else None

def get_last_holiday_update():
    """Get the timestamp of the last holiday update."""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT MAX(cache_date) as last_update FROM holidays')
    result = cursor.fetchone()
    
    if result and result['last_update']:
        return datetime.fromisoformat(result['last_update'])
    return None