/** @odoo-module **/

import { registry } from "@web/core/registry";

/**
 * Browser Print handler registered as a client action.
 * Called when action_print returns tag = vpa_label_designer.browser_print.
 * Runs entirely in the browser — fetches Browser Print SDK on localhost,
 * sends ZPL, shows a notification toast, and closes the wizard dialog.
 */
async function browserPrintHandler(env, action) {
    const params = action.params || {};
    const url = (params.browser_print_url || "https://localhost:9101").replace(/\/$/, "");
    const deviceName = params.device_name || "";
    const zplData = params.zpl_data || "";
    const notification = env.services.notification;

    try {
        const resp = await fetch(`${url}/available`);
        if (!resp.ok) throw new Error(`Browser Print returned ${resp.status}`);
        const data = await resp.json();
        const printers = data.printer || [];

        if (!printers.length) {
            notification.add("No Zebra printers found. Is Browser Print running?", {
                title: "Printer Not Found",
                type: "danger",
                sticky: true,
            });
            env.services.action.doAction({ type: "ir.actions.act_window_close" });
            return;
        }

        let printer = printers[0];
        if (deviceName) {
            const match = printers.find(p => p.name === deviceName);
            if (match) printer = match;
        }

        const writeResp = await fetch(`${url}/write`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ device: printer, data: zplData }),
        });
        if (!writeResp.ok) throw new Error(`Write failed: ${writeResp.status}`);

        notification.add(`Print job sent to ${printer.name}`, {
            title: "Printing...",
            type: "success",
            sticky: false,
        });

    } catch (e) {
        notification.add(e.message || "Failed to connect to Zebra Browser Print", {
            title: "Print Failed",
            type: "danger",
            sticky: true,
        });
    }

    env.services.action.doAction({ type: "ir.actions.act_window_close" });
}

registry.category("actions").add("vpa_label_designer.browser_print", browserPrintHandler);
