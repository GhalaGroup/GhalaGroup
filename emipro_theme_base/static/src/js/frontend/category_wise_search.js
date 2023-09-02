odoo.define('emipro_theme_base.category_wise_search', function(require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var productsSearchBar = publicWidget.registry.productsSearchBar

    productsSearchBar.include({
        events: _.extend({}, productsSearchBar.prototype.events, {
            //'change .ept-parent-category': '_onInput',
            'click .ept-category-a': 'change_category',
        }),
        change_category: function() {
            if (this.$input.val()){
                this._onInput();
            }
        },
        _fetch: function () {
            /*var val ={
                'term' : this.$input.val(),
                'cat_id' : this.$('.ept-parent-category:visible option:selected').val()
            }*/
            return this._rpc({
                route: '/shop/products/autocomplete',
                params: {
                    'term': this.$input.val(),
                    'options': {
                        'order': this.order,
                        'limit': this.limit,
                        'display_description': this.displayDescription,
                        'display_price': this.displayPrice,
                        'max_nb_chars': Math.round(Math.max(this.autocompleteMinWidth, parseInt(this.$el.width())) * 0.22),
                        'cat_id' : this.$el.find('.te_advanced_search_div .dropdown-menu a.dropdown-item.active').attr('value')
                    },
                },
            });
        },
    });
});