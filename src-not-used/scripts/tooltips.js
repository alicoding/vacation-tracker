/**
 * Fix tooltip flickering and double tooltip issues
 */
document.addEventListener('DOMContentLoaded', () => {
  // Use a small delay to prevent flickering
  let tooltipTimeout;
  
  // Find all tooltip triggers
  const tooltipTriggers = document.querySelectorAll('.tooltip-trigger');
  
  tooltipTriggers.forEach(trigger => {
    trigger.addEventListener('mouseenter', () => {
      clearTimeout(tooltipTimeout);
      tooltipTimeout = setTimeout(() => {
        // Hide any other visible tooltips first
        document.querySelectorAll('.tooltip.visible').forEach(t => {
          if (!trigger.contains(t)) {
            t.classList.remove('visible');
          }
        });
        
        // Show this tooltip
        const tooltip = trigger.querySelector('.tooltip');
        if (tooltip) {
          tooltip.classList.add('visible');
        }
      }, 50); // Small delay to prevent flickering
    });
    
    trigger.addEventListener('mouseleave', () => {
      clearTimeout(tooltipTimeout);
      tooltipTimeout = setTimeout(() => {
        const tooltip = trigger.querySelector('.tooltip');
        if (tooltip) {
          tooltip.classList.remove('visible');
        }
      }, 50);
    });
  });
});
