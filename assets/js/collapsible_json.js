/**
 * Collapsible JSON viewer for Django admin
 * Automatically initializes all collapsible JSON elements on the page
 */

(function() {
    'use strict';

    /**
     * Initialize a single collapsible JSON element
     * @param {string} widgetId - The unique ID for this widget instance
     */
    function initCollapsibleJson(widgetId) {
        const toggle = document.getElementById(widgetId + '_toggle');
        const content = document.getElementById(widgetId + '_content');
        
        if (!toggle || !content) {
            return;
        }

        toggle.addEventListener('click', function() {
            // Check computed style instead of inline style to handle CSS-defined display
            const isHidden = content.style.display === 'none' || 
                           window.getComputedStyle(content).display === 'none';
            
            if (isHidden) {
                content.style.display = 'block';
                toggle.textContent = 'Masquer JSON';
            } else {
                content.style.display = 'none';
                toggle.textContent = 'Afficher JSON';
            }
        });
    }

    /**
     * Initialize all collapsible JSON elements on the page
     */
    function initAllCollapsibleJson() {
        // Find all toggle buttons with IDs matching the pattern
        const toggleButtons = document.querySelectorAll('[id$="_toggle"]');
        
        toggleButtons.forEach(function(button) {
            const buttonId = button.id;
            if (buttonId.startsWith('json_api_data_') && buttonId.endsWith('_toggle')) {
                // Extract the widget ID (remove '_toggle' suffix)
                const widgetId = buttonId.slice(0, -7);
                initCollapsibleJson(widgetId);
            }
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAllCollapsibleJson);
    } else {
        // DOM is already ready
        initAllCollapsibleJson();
    }

    // Re-initialize when Django admin uses inline forms (for dynamic forms)
    if (typeof django !== 'undefined' && django.jQuery) {
        django.jQuery(document).on('formset:added', function() {
            initAllCollapsibleJson();
        });
    }
})();
