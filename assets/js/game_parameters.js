/**
 * Game Parameters Widget JavaScript
 * Handles form submission for game parameter fields
 */

(function() {
    'use strict';

    /**
     * Initialize game parameters form handling for a specific widget
     * @param {string} fieldName - The name of the hidden field
     * @param {Object} schema - The parameter schema with field types
     */
    function initGameParameters(fieldName, schema) {
        var hiddenField = document.getElementById('id_' + fieldName);
        if (!hiddenField) {
            return;
        }

        var form = hiddenField.closest('form');
        if (!form) {
            return;
        }

        // Add submit event listener
        form.addEventListener('submit', function() {
            var params = {};
            
            // Collect values from all parameter fields
            for (var paramName in schema) {
                if (schema.hasOwnProperty(paramName)) {
                    var fieldId = 'param_' + paramName;
                    var field = document.getElementById(fieldId);
                    var paramType = schema[paramName].type || 'string';
                    
                    if (field) {
                        if (paramType === 'bool') {
                            params[paramName] = field.checked;
                        } else if (paramType === 'int') {
                            params[paramName] = parseInt(field.value, 10);
                        } else {
                            params[paramName] = field.value;
                        }
                    }
                }
            }
            
            // Update hidden field with JSON string
            hiddenField.value = JSON.stringify(params);
        });
    }

    /**
     * Initialize all game parameter widgets on the page
     */
    function initAllGameParameters() {
        var widgets = document.querySelectorAll('[data-game-parameters]');
        widgets.forEach(function(widget) {
            var fieldName = widget.getAttribute('data-field-name');
            var schemaJson = widget.getAttribute('data-schema');
            
            if (fieldName && schemaJson) {
                try {
                    var schema = JSON.parse(schemaJson);
                    initGameParameters(fieldName, schema);
                } catch (e) {
                    console.error('Failed to parse game parameters schema:', e);
                }
            }
        });
    }

    // Initialize on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAllGameParameters);
    } else {
        initAllGameParameters();
    }

    // Support for Django inline forms
    if (typeof django !== 'undefined' && django.jQuery) {
        django.jQuery(document).on('formset:added', function() {
            initAllGameParameters();
        });
    }
})();
