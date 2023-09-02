odoo.define('slider.builder.helper', function (require) {
'use strict';
var WysiwygMultizone = require('web_editor.wysiwyg.multizone');
var rpc = require('web.rpc');

     WysiwygMultizone.include({
            start: function () {
                $(document).on('change', '#snippets_list_allproduct .form-control, #snippets_list_product .form-control,#snippets_list_category .form-control,#snippets_list_best_seller .form-control,#snippets_list_new_product .form-control,#snippets_list_category_products .form-control',function(){
                    $(this).parents("form").find(".te_style_image_block").attr("class","te_style_image_block style-"+this.value);
                });
                $('.common_carousel_emp_ept').carousel();
                $('.common_carousel_emp_ept').carousel({
                  interval: 3000
                });
                $('.common_carousel_emp_ept .carousel-item').each(function(){
                    $(this).children().not(':first').remove();

                    for (var i=0;i<2;i++) {
                        $(this).children().not(':first').remove();
                    }
                });

                $("#top_menu > .dropdown").each(function() {
                    $(this).hover(function() {
                        $(this).removeClass('open');
                    });
                });

                if($('#id_lazyload').length) {
                    $('img.lazyload').each(function(){
                        var getDataSrcVal = $(this).attr('data-src');
                        if(getDataSrcVal == undefined || getDataSrcVal != ''){
                            $(this).attr('src', getDataSrcVal);
                            $(this).attr('data-src', '');
                        }
                    });
                }

                return this._super.apply(this, arguments);
            },
        /**
         * @override
         */
            _saveElement: function (outerHTML, recordInfo, editable) {
                var promises = [];

                var $el = $(editable);
                var oldHtml = $(outerHTML);
                oldHtml.find("[data-isemipro='true'],.te_brand_slider,.te_category_slider").empty();
                /* Apply Lazyload for all snippet images*/
                if($('#id_lazyload').length) {
                    if(oldHtml){
                        $.each(oldHtml.find('img.lazyload'), function(index, value){
                            var getDataSrcVal = $(value).attr('data-src');
                            var getSrcVal = $(value).attr('src');
                            var getClass = $(value).attr('class');
                            var getWeb = $('.current_website_id').val();
                            if(getDataSrcVal == undefined || getDataSrcVal != ''){
                                $(value).attr('src', '/web/image/website/'+ getWeb +'/lazy_load_image');
                                $(value).attr('data-src', getSrcVal);
                            }
                        });
                    }
                }
                var updateHtml = oldHtml[0].outerHTML;
                // Saving a view content
                var viewID = $el.data('oe-id');
                if (viewID) {
                    promises.push(this._rpc({
                        model: 'ir.ui.view',
                        method: 'save',
                        args: [
                            viewID,
                            updateHtml,
                            $el.data('oe-xpath') || null,
                        ],
                        context: recordInfo.context,
                    }));
                }

                // Saving mega menu options
                if ($el.data('oe-field') === 'mega_menu_content') {
                    // On top of saving the mega menu content like any other field
                    // content, we must save the custom classes that were set on the
                    // menu itself.
                    // FIXME normally removing the 'show' class should not be necessary here
                    // TODO check that editor classes are removed here as well
                    var classes = _.without($el.attr('class').split(' '), 'dropdown-menu', 'o_mega_menu', 'show');
                    promises.push(this._rpc({
                        model: 'website.menu',
                        method: 'write',
                        args: [
                            [parseInt($el.data('oe-id'))],
                            {
                                'mega_menu_classes': classes.join(' '),
                            },
                        ],
                    }));
                }

                // Saving cover properties on related model if any
                var prom = this._saveCoverProperties(editable);
                if (prom) {
                    promises.push(prom);
                }

                return Promise.all(promises);
            }
        });
});