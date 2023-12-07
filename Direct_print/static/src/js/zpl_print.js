console.log('in test js');
odoo.define('layla', function (require) {
    "use strict";

    var core = require('web.core');
    var framework = require('web.framework');
    var session = require('web.session');
    var ActionManager = require('web.ActionManager');

    require("web.ReportActionManager");

    ActionManager.include({
        _triggerPrint: function (action, options, type) {
            let reportUrls = this._makeReportUrls(action);
            let reportUrl = reportUrls[type];
            return this._printReport(reportUrl, action, options).then(() => {
                if (action.close_on_report_download) {
                    const closeAction = { type: 'ir.actions.act_window_close' };
                    return this.doAction(closeAction, _.pick(options, 'on_close'));
                } else {
                    return options.on_close();
                }
            });
        },

        _printReport: function (url, action, options) {
            const form_data = new FormData();
            var type = 'qweb-' + url.split('/')[2];
            form_data.append('csrf_token', core.csrf_token);
            form_data.append('data', JSON.stringify([url, type]));
            form_data.append('context', JSON.stringify(session.user_context));
            form_data.append('token', 'dummy-because-api-expects-one');

            var self = this;
            framework.blockUI();
            return new Promise(function (resolve, reject) {
                fetch('/report/download', {
                    body: form_data,
                    method: 'POST',
                }).then(response => response.text())
                    .then(report_zpl => {
                        console.debug("Printing the following report data:", report_zpl);

                        return new Promise((resolve) => {
                            self._sendToPrinter(report_zpl).then(resolve).catch((error) => {
                                console.error('Report printing failed ⚠', error);
                                
                                const downloadZPL = confirm(`${error.message}, the report will be downloaded instead.`);
                                if (downloadZPL) self._triggerDownload(action, options, 'text');

                                resolve();
                            });
                        });

                    }).then(() => framework.unblockUI())
                    .catch(err => {
                        framework.unblockUI()
                        self.call('crash_manager', 'rpc_error', err);
                        reject();
                    });
            });
        },

        /**
         * Sends a generated ZPL report to the default Zebra printer so it gets printer.
         * @param {string} zpl_data The ZPL data to print (which is the generated report).
         * @returns A promise which resolves once the document has been printer, or rejects with an error message suitable to display for the user.
         */
        _sendToPrinter: function (zpl_data) {
            return new Promise(function (resolve, reject) {
                // Step one: Get the default printer.
                console.debug('Getting default device... ⚙');
                BrowserPrint.getDefaultDevice('printer', function (device) {
                    // Stop two: Wrap it with the ZebraPrinter, so it's more usage friendly.
                    const printer = new Zebra.Printer(device);

                    // Step three: Check if it's a valid device, or an undefined device (which is provided incase there's no default printer).
                    if (printer.deviceType === undefined) {
                        console.error('The default printer is not set! 😕', printer, device);
                        reject(new Error("Couldn't get the default printer"));
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
                            reject(new Error("An error occured while printing"));
                        });
                    }).catch((error) => {
                        console.error('The printer is not ready! 😐', error);
                        reject(new Error("An error occured while printing"));
                    });

                }, () => reject(new Error("Couldn't get the default printer")));
            });
        },

        _executeReportAction: function (action, options) {
            var self = this;

            if (action.report_type === 'qweb-text') {
                return self._triggerPrint(action, options, 'text');
            }

            return this._super.apply(this, arguments);
        },

    });

})


