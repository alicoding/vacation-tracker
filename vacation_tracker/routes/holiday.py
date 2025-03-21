from flask import Blueprint, flash, redirect, url_for
from vacation_tracker.services.holiday_service import refresh_holiday_cache

holiday_bp = Blueprint('holiday', __name__, url_prefix='/holidays')

@holiday_bp.route('/refresh')
def refresh_holidays():
    """Manually refresh the holiday cache."""
    try:
        total_holidays = refresh_holiday_cache()
        if total_holidays > 0:
            flash(f'Bank holiday data has been successfully updated! Found {total_holidays} bank holidays.', 'success')
        else:
            flash('No bank holidays found. Please try again later or contact support.', 'error')
    except Exception as e:
        flash(f'Error refreshing bank holiday data: {str(e)}', 'error')
    
    return redirect(url_for('main.index')) 