// Holiday data initialization
document.addEventListener('DOMContentLoaded', function() {
    // Add holiday data to the page for JavaScript access
    const holidayData = document.createElement('script');
    holidayData.id = 'holiday-data';
    holidayData.type = 'application/json';
    holidayData.textContent = document.getElementById('holiday_dates').value || '[]';
    document.body.appendChild(holidayData);
    
    // Initialize tooltips for date elements
    initTooltips();
    
    // Calculate vacation metadata (long weekends, holidays)
    calculateVacationMetaInfo();
});

// Enhanced date picker initialization with tooltips
function initDatePicker() {
    const datepicker = document.querySelector('.date-picker');
    if (!datepicker) return;
    
    // Initialize your date picker library here
    
    // Add tooltips and special date highlighting
    const bookedDates = JSON.parse(datepicker.dataset.bookedDates || '[]');
    const holidays = JSON.parse(document.getElementById('holiday-data').textContent || '[]');
    
    // Format dates for the date picker
    const formattedBookedDates = bookedDates.map(date => ({
        date: new Date(date.date),
        className: 'booked-date',
        tooltip: `Booked: ${date.description}`
    }));
    
    const formattedHolidays = holidays.map(holiday => ({
        date: new Date(holiday.date),
        className: holiday.is_bank_holiday ? 'holiday-date bank-holiday' : 'holiday-date',
        tooltip: `${holiday.name}${holiday.is_bank_holiday ? ' (Bank Holiday)' : ''}`
    }));
    
    // Identify overlapping dates
    const dateMap = {};
    [...formattedBookedDates, ...formattedHolidays].forEach(dateObj => {
        const dateStr = dateObj.date.toISOString().split('T')[0];
        if (!dateMap[dateStr]) {
            dateMap[dateStr] = [];
        }
        dateMap[dateStr].push(dateObj);
    });
    
    // Handle special date rendering
    Object.entries(dateMap).forEach(([dateStr, dateObjs]) => {
        if (dateObjs.length > 1) {
            // Multiple events on the same date - create overlap styling
            const dateCell = document.querySelector(`.date-cell[data-date="${dateStr}"]`);
            if (dateCell) {
                dateCell.classList.add('overlap-date');
                dateCell.setAttribute('data-tooltip', dateObjs.map(d => d.tooltip).join(' | '));
            }
        }
    });
    
    // Initialize tooltips
    initTooltips();
}

// Enhanced tooltip initialization
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    const tooltip = document.createElement('div');
    tooltip.className = 'date-tooltip';
    document.body.appendChild(tooltip);
    
    tooltipElements.forEach(el => {
        el.addEventListener('mouseenter', (e) => {
            const text = el.getAttribute('data-tooltip');
            tooltip.textContent = text;
            tooltip.style.opacity = 1;
            positionTooltip(e, tooltip);
        });
        
        el.addEventListener('mousemove', (e) => {
            positionTooltip(e, tooltip);
        });
        
        el.addEventListener('mouseleave', () => {
            tooltip.style.opacity = 0;
        });
    });
    
    // Also support title attributes for browsers that handle them natively
    document.querySelectorAll('[title]').forEach(el => {
        if (!el.hasAttribute('data-tooltip')) {
            el.setAttribute('data-tooltip', el.getAttribute('title'));
        }
    });
}

// Position the tooltip near mouse cursor with improved positioning
function positionTooltip(e, tooltip) {
    const x = e.clientX + 15;
    const y = e.clientY + 15;
    
    // Adjust tooltip position if it would go off screen
    const tooltipWidth = tooltip.offsetWidth || 150;
    const tooltipHeight = tooltip.offsetHeight || 50;
    
    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;
    
    // Check if tooltip would go off the right edge
    const finalX = x + tooltipWidth > windowWidth ? x - tooltipWidth - 30 : x;
    
    // Check if tooltip would go off the bottom edge
    const finalY = y + tooltipHeight > windowHeight ? y - tooltipHeight - 30 : y;
    
    tooltip.style.left = `${finalX}px`;
    tooltip.style.top = `${finalY}px`;
}

// Calculate if a vacation includes a long weekend or is adjacent to holidays
function calculateVacationMetaInfo() {
    const vacationEntries = document.querySelectorAll('.vacation-entry');
    const holidays = JSON.parse(document.getElementById('holiday-data').textContent || '[]');
    
    vacationEntries.forEach(entry => {
        const startDateStr = entry.getAttribute('data-start-date');
        const endDateStr = entry.getAttribute('data-end-date');
        
        if (!startDateStr || !endDateStr) return;
        
        const startDate = new Date(startDateStr);
        const endDate = new Date(endDateStr);
        
        // Check for long weekends (Friday to Monday)
        const includesLongWeekend = checkForLongWeekend(startDate, endDate);
        
        // Check for adjacent holidays
        const adjacentHolidays = checkForAdjacentHolidays(startDate, endDate, holidays);
        
        // Update meta info if indicators aren't already there
        const metaInfo = entry.querySelector('.meta-info');
        
        if (includesLongWeekend && !metaInfo.querySelector('.long-weekend-indicator')) {
            metaInfo.appendChild(createIndicator('long-weekend-indicator', 'Long Weekend', 'Includes a long weekend'));
        }
        
        if (adjacentHolidays.length > 0 && !metaInfo.querySelector('.holiday-adjacent-indicator')) {
            metaInfo.appendChild(createIndicator('holiday-adjacent-indicator', '+Holiday', 'Adjacent to a holiday'));
        }
    });
}

// Helper function to create indicator elements
function createIndicator(className, text, tooltip) {
    const indicator = document.createElement('span');
    indicator.className = className;
    indicator.textContent = text;
    indicator.setAttribute('title', tooltip);
    indicator.setAttribute('data-tooltip', tooltip);
    return indicator;
}

// Check if vacation period includes a long weekend (Friday to Monday)
function checkForLongWeekend(startDate, endDate) {
    // Need at least 3 days for a long weekend
    if ((endDate - startDate) / (1000 * 60 * 60 * 24) < 3) {
        return false;
    }
    
    // Check each day in the range
    let currentDate = new Date(startDate);
    
    while (currentDate <= endDate) {
        const dayOfWeek = currentDate.getDay(); // 0=Sunday, 1=Monday, 5=Friday
        
        // Check if it's Friday and the range includes Monday
        if (dayOfWeek === 5) {
            const monday = new Date(currentDate);
            monday.setDate(monday.getDate() + 3); // Move to Monday
            
            if (monday <= endDate) {
                return true;
            }
        }
        
        // Move to next day
        currentDate.setDate(currentDate.getDate() + 1);
    }
    
    return false;
}

// Check if vacation is adjacent to holidays
function checkForAdjacentHolidays(startDate, endDate, holidays) {
    const adjacentHolidays = [];
    
    // Check the day before the vacation starts
    const dayBefore = new Date(startDate);
    dayBefore.setDate(dayBefore.getDate() - 1);
    const dayBeforeStr = dayBefore.toISOString().split('T')[0];
    
    // Check the day after the vacation ends
    const dayAfter = new Date(endDate);
    dayAfter.setDate(dayAfter.getDate() + 1);
    const dayAfterStr = dayAfter.toISOString().split('T')[0];
    
    if (holidays.includes(dayBeforeStr)) {
        adjacentHolidays.push(dayBeforeStr);
    }
    
    if (holidays.includes(dayAfterStr)) {
        adjacentHolidays.push(dayAfterStr);
    }
    
    return adjacentHolidays;
}

// Initialize everything when the page loads
document.addEventListener('DOMContentLoaded', () => {
    initDatePicker();
    calculateVacationMetaInfo();
});
