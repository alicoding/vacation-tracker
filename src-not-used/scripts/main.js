/**
 * Main application script
 */
document.addEventListener('DOMContentLoaded', () => {
  // Initialize all components
  initializeTooltips();
  initializeVacationProgress();
  
  // Handle responsive layout adjustments
  handleResponsiveLayout();
});

/**
 * Initialize tooltip functionality
 */
function initializeTooltips() {
  // Tooltips are initialized in tooltips.js
  console.log('Tooltips initialized');
}

/**
 * Set the vacation progress bar percentage and color
 */
function initializeVacationProgress() {
  const progressBars = document.querySelectorAll('.vacation-progress__bar');
  
  progressBars.forEach(bar => {
    const widthPercent = parseFloat(bar.style.width);
    
    // Apply color based on percentage
    if (widthPercent < 30) {
      bar.classList.add('vacation-progress__bar--low');
    } else if (widthPercent < 70) {
      bar.classList.add('vacation-progress__bar--medium');
    } else {
      bar.classList.add('vacation-progress__bar--high');
    }
  });
}

/**
 * Handle responsive layout adjustments
 */
function handleResponsiveLayout() {
  const updateLayout = () => {
    const isMobile = window.innerWidth < 768;
    const isTablet = window.innerWidth >= 768 && window.innerWidth < 992;
    
    // Adjust sidebar calendar based on screen size
    const sidebarCalendar = document.querySelector('.sidebar-calendar');
    if (sidebarCalendar) {
      if (isMobile) {
        sidebarCalendar.classList.add('sidebar-calendar--mobile');
      } else {
        sidebarCalendar.classList.remove('sidebar-calendar--mobile');
      }
    }
  };
  
  // Initial call
  updateLayout();
  
  // Update on resize
  window.addEventListener('resize', updateLayout);
}
