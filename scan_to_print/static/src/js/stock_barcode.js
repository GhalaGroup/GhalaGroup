odoo.define('scan_to_print.MainMenu', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var Dialog = require('web.Dialog');
var Session = require('web.session');
var framework = require('web.framework');

var _t = core._t;

let blockBarcodeScan = false;

var MainMenu = AbstractAction.extend({
    contentTemplate: 'main_menu_mod',

    events: {
        "click .o_stock_barcode_menu": function(){
            this.trigger_up('toggle_fullscreen');
            this.trigger_up('show_home_menu');
        },
    },

    init: function(parent, action) {
        this._super.apply(this, arguments);
        this.message_demo_barcodes = action.params.message_demo_barcodes;
    },

    willStart: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            return Session.user_has_group('stock.group_stock_multi_locations').then(function (has_group) {
                self.group_stock_multi_location = has_group;
            });
        });
    },

    start: function() {
        var self = this;
        core.bus.on('barcode_scanned', this, this._onBarcodeScanned);
        return this._super().then(function() {
            if (self.message_demo_barcodes) {
                self.setup_message_demo_barcodes();
            }
        });
    },

    destroy: function () {
        core.bus.off('barcode_scanned', this, this._onBarcodeScanned);
        this._super();
    },

    setup_message_demo_barcodes: function() {
        var self = this;
        // Upon closing the message (a bootstrap alert), propose to remove it once and for all
        self.$(".message_demo_barcodes").on('close.bs.alert', function () {
            var message = _t("Do you want to permanently remove this message ?\
                It won't appear anymore, so make sure you don't need the barcodes sheet or you have a copy.");
            var options = {
                title: _t("Don't show this message again"),
                size: 'medium',
                buttons: [
                    { text: _t("Remove it"), close: true, classes: 'btn-primary', click: function() {
                        Session.rpc('/stock_barcode/rid_of_message_demo_barcodes');
                    }},
                    { text: _t("Leave it"), close: true }
                ],
            };
            Dialog.confirm(self, message, options);
        });
    },

    _onBarcodeScanned: function(barcode) {
        var self = this;
        if (!$.contains(document, this.el) || blockBarcodeScan) {
            return;
        }

        blockBarcodeScan = true;
        framework.blockUI();

        console.log("BARCODE", barcode);

        Session.rpc('/scan_to_print/scan_from_main_menu_mod', {
            barcode: barcode,
        }).then(function(result) {
            console.log('PRODUCT ID',result);
            if (result===false) {
                self.do_warn("Product wasn't found");
                return;
            }
            if (result==='vendor') {
                self.do_warn("This barcode applies to multiple products. Please scan Fashion Ghala barcode.");
                return;
            }


            return self._downloadZplReport(result).then(self._sendToPrinter).catch((error) => {
                console.error('failed to print', error);
                self.do_warn(error.message);
            });
        }).finally(() => {
            framework.unblockUI();
            blockBarcodeScan = false;
        });
    },

    _downloadZplReport: function (id) {
        const url = '/report/text/stock.label_product_product_view/'+id;
        const form_data = new FormData();
        form_data.append('csrf_token', core.csrf_token);
        form_data.append('data', JSON.stringify([url, 'qweb-text']));
        form_data.append('context', JSON.stringify(Session.user_context));
        form_data.append('token', 'dummy-because-api-expects-one');

        return fetch('/report/download', {
            body: form_data,
            method: 'POST',
        }).then(response => response.text());
    },

    /**
     * Sends a generated ZPL report to the default Zebra printer so it gets printer.
     * @param {string} zpl_data The ZPL data to print (which is the generated report).
     * @returns A promise which resolves once the document has been printer, or rejects with an error message suitable to display for the user.
     */
    _sendToPrinter: function (zpl_data) {
        console.log('this is the downloaded zpl:',zpl_data);
        return new Promise(function (resolve, reject) {
            // Step one: Get the default printer.
            console.debug('Getting default device... ⚙');
            BrowserPrint.getDefaultDevice('printer', function (device) {
                // Stop two: Wrap it with the ZebraPrinter, so it's more usage friendly.
                const printer = new Zebra.Printer(device);

                // Step three: Check if it's a valid device, or an undefined device (which is provided incase there's no default printer).
                if (printer.deviceType === undefined) {
                    console.error('The default printer is not set! 😕', printer, device);
                    reject(new Error("The default printer is not set!"));
                    return;
                }

                console.debug('Got the printer 🖨', device, printer);

                // Step four: Wait for the printer to be ready.
                printer.isPrinterReady().then(() => {

                    // Step five: Send the report to print!
                    console.debug('Sending the report to the printer...');
                    printer.send(zpl_data, () => {

                        // Step six: We're done :)
                        console.debug('Printed report successfully 😊');
                        resolve();
                    }, (error) => {
                        console.error('Failed to print report! 😐', error)
                        reject(new Error("An error occurred while printing."));
                    });
                }).catch((error) => {
                    console.error('The printer is not ready! 😐', error);
                    reject(new Error("An error occurred while printing."));
                });

            }, () => reject(new Error("Couldn't get the default printer.")));
        });
    },
});

core.action_registry.add('scan_to_print_main_menu', MainMenu);

return {
    MainMenu: MainMenu,
};

});
