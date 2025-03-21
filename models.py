# ...existing code...

class Vacation:
    # ...existing code...
    
    @property
    def total_days(self):
        """Calculate the total number of vacation days, including weekends within the period."""
        delta = self.end_date - self.start_date
        return delta.days + 1
    
    @property
    def includes_long_weekend(self):
        """Check if the vacation includes a long weekend."""
        current_date = self.start_date
        while current_date <= self.end_date:
            # Check if it's Friday and Monday is within the vacation period
            if current_date.weekday() == 4:  # Friday
                monday = current_date + timedelta(days=3)
                if monday <= self.end_date:
                    return True
            current_date += timedelta(days=1)
        return False
    
    @property
    def adjacent_holiday(self):
        """Check if the vacation is adjacent to a holiday."""
        from app import get_holidays  # Import here to avoid circular imports
        
        holidays = get_holidays()
        holiday_dates = [h['date'] for h in holidays]
        
        # Check the day before the vacation starts
        day_before = self.start_date - timedelta(days=1)
        if day_before in holiday_dates:
            return True
            
        # Check the day after the vacation ends
        day_after = self.end_date + timedelta(days=1)
        if day_after in holiday_dates:
            return True
            
        return False

# ...existing code...
