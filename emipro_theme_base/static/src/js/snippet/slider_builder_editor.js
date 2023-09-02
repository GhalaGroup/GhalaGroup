//--------------------------------------------------------------------------
// Dynamic Slider Builder Editor  Configuration
//--------------------------------------------------------------------------
odoo.define('slider.builder.editor', function (require) {
'use strict';

    var rpc = require('web.rpc');
    var options = require('web_editor.snippets.options');
    var wUtils = require('website.utils');
    var ajax = require('web.ajax');
    // Product Slider Editor
    options.registry.product_list_slider = options.Class.extend({
        edit_slider : function (is_new){
            var self = this;
            $('.cus_theme_loader_layout').removeClass('d-none')
            $("#product_configure_model_main").empty()
            ajax.jsonRpc('/get-slider-template', 'call').then(function(data) {
                $("#product_configure_model_main").html(data) // add model popup data
                $('.cus_theme_loader_layout').addClass('d-none')
                $('#product_configure_model').modal('show');
                $('#product_configure_model').on('shown.bs.modal', function (event) {
                    $(this).find('h4').click()
                })
                $('.product-config-content').click(function(e) {
                    // Set description and heading
                    $('.config-note > div').html($(this).attr('data-description'))
                    $('.config-note > h3').html($(this).attr('data-heading'))
                    $('.product-config-content,.product-configure').removeClass('active')
                    $(".product-configure").removeClass('d-none')
                    $(".js-manual-conf-btn,.product-box").addClass('d-none')
                    $(this).addClass('active')
                    if($(this).attr('data-value') === 'manual-configuration') {
                        $(".product-configure").addClass('d-none') //show the input element for manual configuration
                        $(".js-manual-conf-btn,.product-box").removeClass('d-none')
                        // While editing the slider add the selected products
                        if(!is_new){
                             $(".product-box .products").remove()
                             var product_ids = self.$target.attr('data-product_ids') || false;
                             if(product_ids.length){
                                product_ids = product_ids.split(',').map(function(e) {return +parseInt(e)})
                                ajax.jsonRpc('/get-products-of-slider', 'call' , {'product_ids': product_ids,}).then(function(data) {
                                    if (data){
                                    $.each(data, function(i, item) {
                                        $(".js_new_item").before('<li class="js_items products" value ='+item[0]+' >'+item[1]+'<a class="close"></a>'+'</li>');
                                    });
                                    }
                                })
                          }
                        }
                    }
                    if($(this).attr('data-value') === 'product-category-discount') {
                         $('.category-discount input:checkbox').on('click', function(e) {
                             e.stopImmediatePropagation();
                             var checked = (e.currentTarget.checked) ? false : true;
                             e.currentTarget.checked=(checked) ? false : checked.toString();
                         });
                         $(".product-configure").addClass('d-none')
                         $(".category-discount").removeClass('d-none')
                         $(".js-manual-conf-btn").removeClass('d-none')
                         if(!is_new){
                             var category_ids = self.$target.attr('data-category_ids') || false;
                             var discount_policy = self.$target.attr('data-discount_policy')
                             if(category_ids.length){
                                category_ids = category_ids.split(',').map(function(e) {return +parseInt(e)})
                                $('.slider_category_list').val(category_ids).click()
                             }
                             else {
                                $(".slider_category_list").val($(".slider_category_list option:first").val());
                             }
                             if(discount_policy == 'discounts') {
                                $('.category-discount input:checkbox').click()
                             }
                         } else {
                            $(".slider_category_list").val($(".slider_category_list option:first").val());
                         }
                    }

                    if($(this).attr('data-value') === 'custom-domain') {
                            $('.slider_filter_option  a').on('click', function(e) {
                                $('.slider_filter_option a').removeClass('active');
                                $(this).addClass('active');
                                $('.dropdown .slider-filter-ui').text($(this).text());
                            });
                             $(".product-configure").addClass('d-none')
                             $(".custom-domain").removeClass('d-none')
                             $(".js-manual-conf-btn").removeClass('d-none')
                             if(!is_new){
                                var filter_id = self.$target.attr('data-filter_id');
                                if($('.slider_filter_option  a[data-filter="'+filter_id +'"]').length > 0)
                                {
                                    $('.slider_filter_option  a[data-filter="'+filter_id +'"]').trigger('click')
                                }
                                else
                                {
                                    $('.slider_filter_option .dropdown-item').first().click()
                                }
                             }
                    }
                    // UI style selection
                });

                // Set product slider if any otherwise first
                var name = self.$target.attr("data-name") || false;
                if($('.product-config-content[data-value="'+name+'"]').length > 0 && name)
                    $('.product-config-content[data-value="'+name+'"]').trigger('click')
                else
                    $('.product-config-content').first().click();
                
                // While click On UI config
                $('.js-ui-config').on('click', function(e) {
                    $('.product_slider_configure_template').hide();
                    $('.product_ui_configure_template').show();
                    render_ui_section(1);
                });

                // Go to the UI configure section
                function render_ui_section(flag) {
                    if(flag) {
                        $('.cus_theme_loader_layout').removeClass('d-none')
                        name= $('.product_slider_configure_template .product-config-content.active').attr('data-value')
                        ajax.jsonRpc('/get-first-product', 'call' , {}).then(function(data) {
                            $('#product-slider-configure').html(data)
                            $('.cus_theme_loader_layout').addClass('d-none')
                            // Return to product-configuration
                            $('.js-product-config').on('click', function(e) {
                                $('.product_slider_configure_template').show();
                                $('.product_ui_configure_template').hide();
                            });
                            
                            // UI style selection 
                            $('#product-slider-configure .slider_style_option  a').on('click', function(e) {
                                $('#product-slider-configure .dropdown-menu a').removeClass('active');
                                $(this).addClass('active');
                                $('.product_ui_configure_template .dropdown .slider-style-ui').text($(this).text());
                                var template = $(this).attr('data-value')
                                getSliderStyle(template)
                            });
                            getActiveButton()
                            // UI option selection 
                            $('.slider-ui-icon .product-config-icon').on('click', function(e) {
                                $(this).toggleClass('active')
                                renderuielement();
                            })

                            // UI set limit
                            $('#product-slider-configure .slider_limit_option  a').on('click', function(e) {
                                $('#product-slider-configure .slider_limit_option a').removeClass('active');
                                $(this).addClass('active');
                                $('.product_ui_configure_template .dropdown .slider-product-limit').text($(this).text());
                            });

                            // UI sort option
                            $('#product-slider-configure .slider_sort_option  a').on('click', function(e) {
                                $('#product-slider-configure .slider_sort_option a').removeClass('active');
                                $(this).addClass('active');
                                $('.product_ui_configure_template .dropdown .slider-sort-by').text($(this).text());
                            });
                             if(name !== 'custom-domain'){
                                  $('.product_ui_configure_template .div_sort_by').removeClass('d-inline-block').addClass('d-none')
                             }
                             else{
                                  $('.product_ui_configure_template .div_sort_by').addClass('d-inline-block').removeClass('d-none')
                             }
                             if(name === 'manual-configuration'){
                                  $('.product_ui_configure_template .js_product_limit').removeClass('d-inline-block').addClass('d-none')
                             }
                             else{
                                  $('.product_ui_configure_template .js_product_limit').addClass('d-inline-block').removeClass('d-none')
                             }

                            // set default style 
                            var style_template = self.$target.attr('data-style-template')
                            if($('.slider_style_option  [data-style="'+style_template +'"]').length > 0)
                               $('.slider_style_option [data-style="'+style_template +'"]').trigger('click')
                            else
                               $('#product-slider-configure .slider_style_option  a').first().click()

                            var limit = self.$target.attr('data-limit')
                            if($('.slider_limit_option  [data-value="'+limit +'"]').length > 0)
                               $('.slider_limit_option [data-value="'+limit +'"]').trigger('click')
                            else
                               $('#product-slider-configure .slider_limit_option  a').first().click()

                            var sort_by = self.$target.attr('data-sort_by')
                            if($('.slider_sort_option  [data-value="'+sort_by +'"]').length > 0)
                               $('.slider_sort_option [data-value="'+sort_by +'"]').trigger('click')
                            else
                               $('#product-slider-configure .slider_sort_option  a').first().click()

                            // Save slider data
                            $(".js-save-config").on('click', function(ev) {
                                ev.preventDefault();
                                self.$target.removeAttr("data-product_ids")
                                self.$target.removeAttr("data-filter")
                                self.$target.removeAttr("data-sort_by")
                                self.$target.removeAttr("data-category_ids")
                                self.$target.removeAttr("data-discount_policy")
                                var slider_type =$(".product-config-content.active").data('value')
                                var slider_style_template =$(".slider_style_option .dropdown-item.active").data('style')
                                var slider_filter =$(".slider_filter_option .dropdown-item.active").data('filter')
                                var slider_limit =$(".slider_limit_option .dropdown-item.active").data('value')
                                var slider_sort_by =$(".slider_sort_option .dropdown-item.active").data('value')
                                var slider_categ_id = $('.category-discount .slider_category_list').val()
                                var selected_ui_options = [];
                                var product_ids = [];
                                $('.ui-settings .product-config-icon.active').each(function(){
                                    selected_ui_options.push($(this).data('value'));
                                });
                                if (slider_type === 'manual-configuration')
                                {
                                    $('.product-box li.products').each(function(){
                                         product_ids.push($(this).val());
                                    });
                                    self.$target.attr("data-product_ids", product_ids);
                                }
                                if (slider_type === 'custom-domain')
                                {
                                self.$target.attr("data-sort_by", slider_sort_by);
                                self.$target.attr("data-filter_id", slider_filter);
                                }
                                if (slider_type === 'product-category-discount')
                                {
                                self.$target.attr("data-category_ids", slider_categ_id);
                                self.$target.attr("data-discount_policy",$('.category-discount input[type="checkbox"]:checked').length > 0 ? 'discounts':'products')
                                }
                                self.$target.attr("data-name", slider_type);
                                self.$target.attr("data-limit", slider_limit);
                                self.$target.attr("data-style-template", slider_style_template);
                                self.$target.attr("data-ui-option", selected_ui_options);
                                $('#product_configure_model').modal('hide');
                            })
                        });
                    }
                }

                // Select slider style while change from dropdown
                function getSliderStyle(template) {
                $('.cus_theme_loader_layout').removeClass('d-none')
                    if(template) {
                        ajax.jsonRpc('/get-product-slider-template', 'call' , {'template': template,}).then(function(data) {
                           $('.cus_theme_loader_layout').addClass('d-none')
                           var slider_main = $(data).find(".js_item").first();
                           $('.ui-preview').html(data);
                           renderuielement();
                        })
                    }
                }

                function renderuielement(){
                    $('.slider-ui-icon .product-config-icon').each(function(e) {
                        var data_icon = $(this).attr('data-icon')
                        if(!$(this).hasClass('active'))
                            $('.ui-preview .te_pc_style_main').find('.'+data_icon).removeClass('d-none').addClass('d-none')
                        else
                            $('.ui-preview .te_pc_style_main').find('.'+data_icon).removeClass('d-none')
                    });
                }

                // Toggle active class for button
                function getActiveButton() {
                    var ui_option = self.$target.attr('data-ui-option') || false;
                    // if UI option set the set ui option as per that 
                    if(ui_option)
                    {
                        ui_option = ui_option.split(',')
                        var option_ele = $('.slider-ui-icon .product-config-icon')
                        $('.slider-ui-icon .product-config-icon').each(function(i, obj) {
                            if(ui_option.includes($(this).data('value'))){
                                $(this).addClass('active')
                            }
                        });
                    }
                    else
                    {
                        $('.slider-ui-icon .product-config-icon').each(function(i, obj) {
                            $(this).addClass('active')
                        }); 
                    }
                    renderuielement()
                }

                /* Manual Configuration */
                // If the manual config click
                $('.js-manual-conf-btn').on('click', function(e) {
                    $(".product-configure").removeClass('d-none')
                    $(".js-manual-conf-btn").addClass('d-none')
                    $(".custom-domain").addClass('d-none')
                    $(".js_item_box").addClass('d-none')
                    $(".category-discount").addClass('d-none')
                })
                // Add the product
                $('.js_input_item').bind("keyup",function (ev) {
                    var val = $('.js_input_item').val()
                    if(val.length >= 1 && ev.keyCode  != 13){
                        var product_ids = [];
                        $('li.js_items').each(function(){
                             product_ids.push($(this).val());
                        });
                        appendData(val,product_ids)
                    }
                });
                // Delete item element
                $(".js_item_box").on("click", ".close", function(ev)  {
                      $(this).parent().remove();
                });
                // Focus On input Field
                $(".js_item_box").click(function(){
                      $('.js_input_itemt').focus();
                });

                //Sorting item element 
                $(function() {
                    $(".js_item_box").sortable({
                       items: "li:not(.js_new_item)",
                       containment: "parent",
                       scrollSpeed: 100
                    });
                    $(".js_item_box").disableSelection();
                });

                // Add the suggested Product while searching
                function appendData(key,exclude_products) {
                    ajax.jsonRpc('/get-suggested-products', 'call',{'key':key,'exclude_products':exclude_products}).then(function(data) {
                         $("#js_item").empty().removeClass('show')
                         $.each(data, function(i, item) {
                            $('#js_item').addClass('dropdown-menu show')
                            $("#js_item").append("<div class='dropdown-item input-item-link' data-item_id="+item[0]+" data-item_name='"+item[1]+"'>"+item[1]+"</div>")
                         });
                         if(data.length == 0)
                         {
                            $('#js_item').addClass('dropdown-menu show')
                            $("#js_item").append("<div class='dropdown-item' >No result found</div>")
                         }
                         // Add the product as list item
                         $(".input-item-link").on('click',async function (ev) {
                               var val = $(this).attr('data-item_id');
                               var name = $(this).attr('data-item_name');
                               $(".js_new_item").before('<li class="js_items products" value ='+val+' >'+name+'<a class="close"></a>'+'</li>');
                               $('.js_input_item').val('')
                               $("#js_item").empty().removeClass('show')
                         });
                    })
                }
            });
        },
        onBuilt: function () {
            var self = this;
            this._super();
            this.edit_slider(true)
        },
    })
})