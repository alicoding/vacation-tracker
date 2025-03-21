"""
DEPRECATED: This monolithic app has been restructured into the vacation_tracker package.
Please use run.py as the entry point instead.

This file is kept for backward compatibility and will be removed in a future version.
"""

import warnings
from vacation_tracker import create_app

warnings.warn(
    "Using deprecated app.py entry point. Please use run.py instead.",
    DeprecationWarning,
    stacklevel=2
)

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5002)