/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState } from "@odoo/owl";

/**
 * Zebra Browser Print Client Action
 *
 * Sends ZPL data to a local Zebra Browser Print SDK instance.
 * The SDK runs as a service on the user's machine at localhost:9101.
 */
class ZebraBrowserPrintAction extends Component {
    static template = "vpa_label_designer.ZebraBrowserPrintAction";

    setup() {
        this.state = useState({
            status: "connecting",
            message: "Connecting to Zebra Browser Print...",
            printers: [],
            error: null,
        });

        const params = this.props.action.params || {};
        this.zplData = params.zpl_data || "";
        this.browserPrintUrl = params.browser_print_url || "http://localhost:9101";
        this.deviceName = params.device_name || "";
        this.printerName = params.printer_name || "Browser Print";

        this._connectAndPrint();
    }

    async _connectAndPrint() {
        try {
            // Step 1: Get available printers
            this.state.status = "connecting";
            this.state.message = "Discovering printers via Browser Print SDK...";

            const printers = await this._getAvailablePrinters();
            this.state.printers = printers;

            if (printers.length === 0) {
                this.state.status = "error";
                this.state.error = "No Zebra printers found. Please check that Zebra Browser Print is running and a printer is connected.";
                return;
            }

            // Step 2: Select printer
            let selectedPrinter = printers[0];
            if (this.deviceName) {
                const match = printers.find(p => p.name === this.deviceName);
                if (match) selectedPrinter = match;
            }

            // Step 3: Send ZPL
            this.state.status = "printing";
            this.state.message = `Sending ZPL to ${selectedPrinter.name}...`;

            await this._sendToPrinter(selectedPrinter, this.zplData);

            this.state.status = "success";
            this.state.message = `Print job sent to ${selectedPrinter.name} successfully!`;

        } catch (e) {
            this.state.status = "error";
            this.state.error = e.message || "Failed to connect to Zebra Browser Print";
        }
    }

    async _getAvailablePrinters() {
        const response = await fetch(`${this.browserPrintUrl}/available`, {
            method: "GET",
            headers: { "Content-Type": "application/json" },
        });

        if (!response.ok) {
            throw new Error(`Browser Print SDK returned ${response.status}`);
        }

        const data = await response.json();
        return data.printer || [];
    }

    async _sendToPrinter(printer, zplData) {
        const response = await fetch(`${this.browserPrintUrl}/write`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                device: printer,
                data: zplData,
            }),
        });

        if (!response.ok) {
            throw new Error(`Failed to send print job: ${response.status}`);
        }
    }

    onClose() {
        this.props.action.doAction({ type: "ir.actions.act_window_close" });
    }
}

registry.category("actions").add("vpa_label_designer.browser_print", ZebraBrowserPrintAction);
