/** @odoo-module */
import {_printReport} from "direct_print/static/src/views/form/form_controller.js";
import { ErrorDialog } from "@web/core/errors/error_dialogs";
import {registry} from '@web/core/registry';



registry
    .category("ir.actions.report handlers")
    .add("pdf_report_options_handler", async function (action, options, env) {
        if (action.direct_print && action.report_name == "stock.label_product_product_view" || action.report_name == "product_inventory_label.label_product_inventory_view" && action.report_type == "qweb-text" ){
            try {
                console.log("Action",action.report_name )
                await _printReport(action, env)
            } catch (error) {
                env.services.dialog.add(ErrorDialog, {
                    traceback: error.message,
                });
            }

            return true
        }
    })