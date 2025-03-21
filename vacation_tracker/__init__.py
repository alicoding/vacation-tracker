from flask import Flask
from datetime import datetime, date

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
    
    # Register date filter
    @app.template_filter('date')
    def date_filter(value, format='%B %d, %Y'):
        """Format a date using the given format."""
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return value
        if isinstance(value, (datetime, date)):
            return value.strftime(format)
        return value
    
    # Import and register blueprints
    from vacation_tracker.routes.main import main_bp
    from vacation_tracker.routes.holiday import holiday_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(holiday_bp)
    
    # Initialize the database
    from vacation_tracker.utils.db import init_app
    init_app(app)
    
    # Initialize holiday data
    with app.app_context():
        from vacation_tracker.services.holiday_service import get_cached_holidays
        get_cached_holidays(force_refresh=True)
    
    return app