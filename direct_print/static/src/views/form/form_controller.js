/** @odoo-module */
import { ErrorDialog } from "@web/core/errors/error_dialogs";
import { registry } from '@web/core/registry';
const core = require('web.core');



function _sendToPrinter(zpl_data) {
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
}

async function _printReport(action,env) {
    const url = _getReportUrl(action, "text");
    env.services.ui.block();
    try {
        const form_data = new FormData();
        form_data.append('csrf_token', core.csrf_token);
        form_data.append('data', JSON.stringify([url, action.report_type]));
        form_data.append('context', JSON.stringify(action.context));
        form_data.append('token', 'dummy-because-api-expects-one');
        const res = await fetch('/report/download', { body: form_data, method: 'POST' })
        const text = await res.text()
        await _sendToPrinter(text)
    } catch (err) {
        throw err
    }
    finally {
        env.services.ui.unblock();
    }

}
function _getReportUrl(action, type) {
    let url = `/report/${type}/${action.report_name}`;
    const actionContext = action.context || {};
    if (action.data && JSON.stringify(action.data) !== "{}") {
        // build a query string with `action.data` (it's the place where reports
        // using a wizard to customize the output traditionally put their options)
        const options = encodeURIComponent(JSON.stringify(action.data));
        const context = encodeURIComponent(JSON.stringify(actionContext));
        url += `?options=${options}&context=${context}`;
    } else {
        if (actionContext.active_ids) {
            url += `/${actionContext.active_ids.join(",")}`;
        }
        if (type === "html") {
            const context = encodeURIComponent(JSON.stringify(env.services.user.context));
            url += `?context=${context}`;
        }
    }
    return url;
}

registry
    .category("ir.actions.report handlers")
    .add("pdf_report_options_handler", async function (action, options, env) {
        if (action.direct_print && action.report_name == "stock.label_product_product_view" || action.report_name =="product_inventory_label.label_product_inventory_view"  && action.report_type == "qweb-text" ){
            try {
                await _printReport(action, env)
            } catch (error) {
                env.services.dialog.add(ErrorDialog, {
                    traceback: error.message,
                });
            }

            return true
        }
    })