//--------------------------------------------------------------------------
// Snippet Aos Animation customize Options and Expertise Progress bar 
//--------------------------------------------------------------------------
odoo.define('theme_clarico_vega.snippetEpt', function (require) {
	'use strict';
	var SnippetOption = require('web_editor.snippets.options');

    SnippetOption.Class.include({
        selectClass: function (previewMode, widgetValue, params) {
            for (const classNames of params.possibleValues) {
                if (classNames) {
                    this.$target[0].classList.remove(...classNames.trim().split(/\s+/g));
                }
            }
            if (widgetValue) {
                var data_aos_ept = this.$target.attr('data_aos_ept');
                var data_aos = this.$target.attr('data-aos');

                if(data_aos_ept){
                    this.$target.addClass(widgetValue);
                    this.$target.attr('data_aos_ept',widgetValue);
                }
                else if(data_aos){
                    this.$target[0].classList.add(...widgetValue.trim().split(/\s+/g));
                }
                else{
                    this.$target.addClass(widgetValue);
                    this.$target.attr('data_aos_ept',widgetValue);
                }
            }
        },
    });
});
