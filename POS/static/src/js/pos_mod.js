console.log('in pos modified');

odoo.define('pos',function(require){
"use strict";

const { Context } = owl;
var BarcodeParser = require('barcodes.BarcodeParser');
var BarcodeReader = require('point_of_sale.BarcodeReader');
var PosDB = require('point_of_sale.DB');
var devices = require('point_of_sale.devices');
var concurrency = require('web.concurrency');
var config = require('web.config');
var core = require('web.core');
var field_utils = require('web.field_utils');
var time = require('web.time');
var utils = require('web.utils');



var note;
var checked;
var auth_code;
var models = require('point_of_sale.models');
const _super_paymentline = models.Paymentline.prototype;
const _super_Order = models.Order.prototype;

models.Paymentline = models.Paymentline.extend({
    export_as_JSON: function(){
         auth_code = document.querySelector('input[name="auth_code"]')?.value ?? '';
         note = document.querySelector('input[name="note"]')?.value ?? '';
         checked = document.querySelector('.check')?.checked ?? '';

        const json = _super_paymentline.export_as_JSON.apply(this, arguments);
        json.transaction_id = auth_code;
        json.note = note;

        return json;
    },
});

models.Order = models.Order.extend({
    export_for_printing: function(){
        const json = _super_Order.export_for_printing.apply(this);
        json.auth_code = auth_code;
        json.note = note;
        json.checked = checked;
        return json;

    },
});



});