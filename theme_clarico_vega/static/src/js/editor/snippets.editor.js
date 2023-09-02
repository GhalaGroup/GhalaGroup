odoo.define('theme_clarico_vega.snippet.editor', function (require) {
'use strict';

const {qweb, _t, _lt} = require('web.core');
const Dialog = require('web.Dialog');
const weSnippetEditor = require('web_editor.snippet.editor');
const wSnippetOptions = require('website.editor.snippets.options');
var options = require('web_editor.snippets.options');

const FontFamilyPickerUserValueWidget = wSnippetOptions.FontFamilyPickerUserValueWidget;

    weSnippetEditor.Class.include({
        xmlDependencies: (weSnippetEditor.Class.prototype.xmlDependencies || [])
            .concat(['/website/static/src/xml/website.editor.xml']),
        events: _.extend({}, weSnippetEditor.Class.prototype.events, {
            'click .o_we_customize_theme_btn_ept': '_onThemeTabClickEpt',
        }),
        tabs: _.extend({}, weSnippetEditor.Class.prototype.tabs, {
            THEME_EPT: 'theme-ept',
        }),
        OptionsTabStructureEpt: [
            ['theme-options-ept', _lt("Theme Settings")],
        ],

        /**
         * @override
         */
        _updateLeftPanelContent: function ({content, tab}) {
            this._super(...arguments);
            this.$('.o_we_customize_theme_btn_ept').toggleClass('active', tab === this.tabs.THEME_EPT);
        },

        /**
         * @private
         */
        _onThemeTabClickEpt: async function (ev) {
            this._execWithLoadingEffect(async () => new Promise(resolve => setTimeout(() => resolve(), 0)), false, 0);

            if (!this.topFakeOptionElEpt) {
                let el;
                for (const [elementName, title] of this.OptionsTabStructureEpt) {
                    const newEl = document.createElement(elementName);
                    newEl.dataset.name = title;
                    if (el) {
                        el.appendChild(newEl);
                    } else {
                        this.topFakeOptionElEpt = newEl;
                    }
                    el = newEl;
                }
                this.bottomFakeOptionElEpt = el;
                this.el.appendChild(this.topFakeOptionElEpt);
            }

            // Need all of this in that order so that:
            // - the element is visible and can be enabled and the onFocus method is
            //   called each time.
            // - the element is hidden afterwards so it does not take space in the
            //   DOM, same as the overlay which may make a scrollbar appear.
            this.topFakeOptionElEpt.classList.remove('d-none');
            const editor = await this._activateSnippet($(this.bottomFakeOptionElEpt));
            this.topFakeOptionElEpt.classList.add('d-none');
            editor.toggleOverlay(false);

            this._updateLeftPanelContent({
                tab: this.tabs.THEME_EPT,
            });
        },
    });
    options.registry.ThemeOptionsEpt = options.Class.extend({
        pageOptionName: 'ThemeOptionsEpt',
    });
});
