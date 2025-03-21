# Vacation Tracker

A simple web application to track your vacation days. This application helps you manage your 14 vacation days by allowing you to:
- Add vacation days with optional notes
- View your remaining vacation balance
- Delete vacation days if plans change
- See a clear overview of all booked vacation days
- Edit vacation periods if plans change
- Avoid booking vacations on Canadian bank holidays

## Features

- Clean, intuitive interface
- Visual progress bar showing remaining vacation days
- Seamless date picker for selecting single days or date ranges
- Clear display of vacation periods with duration badges
- Optional notes for vacation days
- Canadian bank holiday integration
- Persistent storage using SQLite database
- Responsive design that works on all devices

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your web browser and navigate to:
```
http://localhost:5002
```

## Usage

1. To add vacation days:
   - Click the date field to open the calendar picker
   - Select a single date by clicking once, or select a date range by clicking and dragging
   - (Optional) Add a note describing the purpose of your vacation
   - Click "Add Vacation Day(s)"
   - The system will automatically calculate the total days and update your balance
   - Canadian bank holidays are marked in orange and cannot be booked as vacation days

2. To edit a vacation period:
   - Click the "Edit" button next to the vacation period you want to modify
   - Update the date(s) and/or note in the edit form
   - Click "Save Changes" to apply your modifications
   - The system will automatically recalculate your remaining vacation days
   - Holidays are marked and cannot be selected

3. To delete a vacation period:
   - Click the "Delete" button next to the vacation period you want to remove
   - Confirm the deletion in the popup dialog
   - The system will automatically update your remaining vacation days

4. View your vacation balance:
   - The top card shows your total days, used days, and remaining days
   - The circular progress bar provides a visual representation of your remaining vacation days
   - Each vacation period shows its duration with a badge

5. Manage Canadian bank holidays:
   - The application automatically fetches and displays Canadian bank holidays
   - Holidays are highlighted in the date picker in orange
   - You can view upcoming holidays in the sidebar
   - Click the "Refresh" button to manually update holiday data
   - Holiday data is automatically refreshed when it's out of date

## Data Storage

The application uses SQLite for data storage. The database file (`vacation.db`) will be created automatically when you first run the application. All your vacation days and notes are stored locally on your machine.

## Holiday Integration

The application integrates with the Nager.Date API to fetch Canadian bank holidays. These holidays are:
- Automatically fetched when you first run the app
- Cached locally in the database to reduce API calls
- Refreshed automatically when the cache is outdated (monthly or when entering a new year)
- Highlighted in the calendar to prevent booking vacations on holidays
- Listed in the sidebar for easy reference 