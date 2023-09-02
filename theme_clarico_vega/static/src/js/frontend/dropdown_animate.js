odoo.define('theme_clarico_vega.dropdown_animate', function (require) {
    "use strict";

    var publicWidget = require('web.public.widget');
    var sAnimations = require('website.content.snippets.animation');

    publicWidget.registry.ScrollTop = sAnimations.Animation.extend({
        selector: '#wrapwrap',
         effects: [{
            startEvents: 'scroll',
            update: '_scrollTop',
        }],
        _scrollTop: function (scroll) {
            if (scroll > 300) {
                $('.scrollup-div').fadeIn();
            } else {
                $('.scrollup-div').fadeOut();
            }
        },
    });

    publicWidget.registry.dropdown_animate= publicWidget.Widget.extend({
        selector: "#wrapwrap",
        start: function () {
            self = this;
            self.showDropdown();
            self.showFooter();
            self.showDropdownCategory();
            setTimeout(function () {
                var addToCart = $('#product_details').find('#add_to_cart').attr('class');
                var buyNow = $('#product_details').find('#buy_now').attr('class');
                $('.prod_details_sticky_div #add_to_cart').attr('class', addToCart);
                $('.prod_details_sticky_div #buy_now').attr('class', buyNow);
            }, 800);
        },
        showDropdown: function() {
            $(".te_custom_submenu").parent("li.nav-item").addClass("dropdown");
            $(".te_custom_submenu").siblings("a.nav-link").addClass("dropdown-toggle").attr("data-toggle", "dropdown");

            $('.te_advanced_search_div .dropdown, .dropdown, .te_header_before_overlay .js_language_selector .dropup, header .js_language_selector .dropup').on('show.bs.dropdown', function(ev) {
                if(!$(ev.currentTarget).parents('#top_menu').find('o_mega_menu_toggle')) {
                    $(this).find('.dropdown-menu').first().stop(true, true).slideDown(150);
                }
            });
            $('.te_advanced_search_div .dropdown, .dropdown, .te_header_before_overlay .js_language_selector .dropup, header .js_language_selector .dropup').on('hide.bs.dropdown', function(ev) {
                if(!$(ev.currentTarget).parents('#top_menu').find('o_mega_menu_toggle')) {
                    $(this).find('.dropdown-menu').first().stop(true, true).slideUp(150);
                }
            });
        },
        showFooter:function(){
            if ($(window).width() < 768){
                $('#footer .row > .footer-column-2 .footer_top_title_div').click(function() {
                  $(this).siblings('.te_footer_info_ept').toggleClass('active');
                  $(this).toggleClass('active');
                });
            }
        },
        showDropdownCategory: function() {
            $(".te_advanced_search_div .dropdown-menu a.dropdown-item").on('click', function(){
              $(this).parents(".dropdown").find('.btn.ept-parent-category .span_category').html($(this).text());
              $('.te_advanced_search_div .dropdown-menu a.dropdown-item').removeClass('active');
              $(this).parents(".dropdown").find('.btn.ept-parent-category .span_category').val($(this).addClass('active').val());
            });
        },
    });

});