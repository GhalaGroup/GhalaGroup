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




var models = require('point_of_sale.models');
const _super_paymentline = models.Paymentline.prototype;

models.Paymentline = models.Paymentline.extend({
    export_as_JSON: function(){
        const note = document.querySelector('input[name="popup_note"]')?.value ?? '';

        const json = _super_paymentline.export_as_JSON.apply(this, arguments);
        json.transaction_id = note;

        return json;
    },
});


});