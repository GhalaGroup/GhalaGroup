/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

/**
 * Label Preview Widget - renders ZPL preview via Labelary API
 * Usage: <field name="zpl_preview" widget="label_preview"/>
 */
class LabelPreviewWidget extends Component {
    static template = "vpa_label_designer.LabelPreviewWidget";
    static props = { ...standardFieldProps };

    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            imageData: null,
            loading: false,
            error: null,
        });
    }

    get zplCode() {
        return this.props.record.data[this.props.name] || "";
    }

    async onPreviewClick() {
        const zpl = this.zplCode;
        if (!zpl) {
            this.state.error = "No ZPL code to preview";
            return;
        }

        this.state.loading = true;
        this.state.error = null;
        this.state.imageData = null;

        try {
            const result = await this.rpc("/vpa_label_designer/preview", {
                zpl_code: zpl,
            });

            if (result.success) {
                this.state.imageData = result.image;
            } else {
                this.state.error = result.error || "Preview failed";
            }
        } catch (e) {
            this.state.error = "Failed to generate preview: " + (e.message || e);
        } finally {
            this.state.loading = false;
        }
    }
}

registry.category("fields").add("label_preview", {
    component: LabelPreviewWidget,
    supportedTypes: ["text"],
});
