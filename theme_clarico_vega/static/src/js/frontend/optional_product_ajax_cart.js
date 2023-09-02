odoo.define('theme_clarico_vega.optional_product_ajax_cart', function (require) {
    "use strict";

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var OptionalProductsModal = require('sale_product_configurator.OptionalProductsModal');
    var flag = 1;

    OptionalProductsModal.include({
    /** Ajax cart for the optional product popup */
        init: function (parent, params) {
            this._super.apply(this, arguments);
            this.isWebsite = params.isWebsite;

            this.dialogClass = 'oe_optional_products_modal' + (params.isWebsite ? ' oe_website_sale' : '');
            setTimeout(function(){
                if($('.oe_optional_products_modal').length && $('#ajax_cart_template').val() == 1) {
                    var ajaxCart = new publicWidget.registry.ajax_cart();
                    if(!parent.attr('class')) {
                        var product_id = $('.oe_optional_products_modal').find('.product_template_id').val();
                        var product_product = $('.oe_optional_products_modal').find('.product_id').val();
                        $(document).on('click', '.modal-footer .btn-secondary', function(){
                            ajaxCart.ajaxCartSucess(product_id, product_product);
                        });
                    } else {
                        var optional_parent = parent.attr('class')
                        optional_parent = optional_parent.replace(" ", ".");
                        var modal_id = $('.'+optional_parent).find('.modal_shown').attr('id');
                        var product_id = $('#'+modal_id).find('.product_template_id').val();
                        var product_product = $('#'+modal_id).find('.product_id').val();
                        $(document).on('click', '#'+modal_id+' .modal-footer .btn-secondary', function(){
                            ajaxCart.ajaxCartSucess(product_id, product_product);
                        });
                    }
                }
                /* Attribute value tooltip */
                $(function () {
                  $('[data-toggle="tooltip"]').tooltip({ animation:true, delay: {show: 300, hide: 100} })
                });
            },1400);
        }
    });

});
