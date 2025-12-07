/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillUpdateProps, useState } from "@odoo/owl";

export class VPAPreviewWidget extends Component {
    static template = "vpa_document_layout.VPAPreviewWidget";
    static props = {
        record: { type: Object },
        readonly: { type: Boolean, optional: true },
        name: { type: String, optional: true },
    };

    setup() {
        this.state = useState({
            previewUrl: this.getPreviewUrl(),
        });

        onWillUpdateProps(() => {
            this.state.previewUrl = this.getPreviewUrl();
        });
    }

    getPreviewUrl() {
        const recordId = this.props.record?.resId;
        if (recordId) {
            return `/vpa/template/preview/${recordId}`;
        }
        return null;
    }

    get iframeSrc() {
        return this.state.previewUrl || "about:blank";
    }
}

registry.category("fields").add("vpa_preview", {
    component: VPAPreviewWidget,
});
