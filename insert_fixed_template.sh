#!/bin/bash

docker exec odoo_postgres psql -U odoo -d odoo << 'SQL'
-- Insert the external layout template with the FIX: "company or env.company"
INSERT INTO ir_ui_view (name, type, key, arch_db, active) VALUES (
    'VPA External Layout 3',
    'qweb',
    'vpa_document_layout.external_layout_vpa_template_3',
    '{"en_US": "<t t-name=\"vpa_document_layout.external_layout_vpa_template_3\">\n    <t t-set=\"vpa_template\" t-value=\"env[''vpa.document.template''].browse(3)\"/>\n    <t t-set=\"company\" t-value=\"company or env.company\"/>\n    <t t-set=\"primary_color\" t-value=\"''#875a7b''\"/>\n    <t t-set=\"secondary_color\" t-value=\"''#21b799''\"/>\n\n    <div t-attf-class=\"article o_report_layout_vpa o_company_#{company.id}_layout\" style=\"font-family: ''Lato'', ''Helvetica'', ''Arial'', sans-serif;\">\n\n        <style type=\"text/css\">\n            .o_report_layout_vpa {\n                position: relative;\n                padding: 40px;\n                min-height: 400px;\n            }\n            .o_report_layout_vpa .page {\n                position: relative;\n                z-index: 2;\n            }\n            .o_report_layout_vpa table.o_main_table {\n                border-collapse: separate;\n                border-spacing: 0;\n                border-radius: 8px;\n                overflow: hidden;\n                border: 2px solid #875a7b;\n            }\n            .o_report_layout_vpa table.o_main_table thead {\n                background-color: #875a7b;\n                color: white;\n                font-weight: bold;\n            }\n            .o_report_layout_vpa table.o_main_table tbody tr:nth-child(even) {\n                background-color: rgba(135, 90, 123, 0.05);\n            }\n        </style>\n\n        <!-- Decorative circle -->\n        <svg t-if=\"true\" style=\"position: absolute; top: -100px; right: -100px; z-index: 0;\" width=\"300\" height=\"300\" xmlns=\"http://www.w3.org/2000/svg\">\n            <circle cx=\"150.0\" cy=\"150.0\" r=\"150.0\" fill=\"#875a7b\" fill-opacity=\"0.25\"/>\n        </svg>\n\n        <!-- Header -->\n        <div t-attf-style=\"position: relative; z-index: 1; padding-bottom: 15px; margin-bottom: 25px; border-bottom: 4px solid #875a7b;\">\n            <div style=\"text-align: right; margin-bottom: 10px;\">\n                <img t-if=\"company.logo\" t-att-src=\"image_data_uri(company.logo)\" style=\"max-width: 250px; max-height: 100px;\" alt=\"Logo\"/>\n            </div>\n            <div style=\"text-align: right; font-size: 9pt; line-height: 1.5;\">\n                <t t-if=\"company.company_details\">\n                    <span t-field=\"company.company_details\"/>\n                </t>\n                <t t-else=\"\">\n                    <span t-field=\"company.partner_id\" t-options=''{\"widget\": \"contact\", \"fields\": [\"address\", \"name\"], \"no_marker\": true}''/>\n                </t>\n            </div>\n        </div>\n\n        <!-- Document content -->\n        <t t-out=\"0\"/>\n\n        <!-- Footer -->\n        <div t-if=\"true\" t-attf-style=\"position: relative; z-index: 1; margin-top: 40px; padding-top: 15px; border-top: 2px solid #21b799; font-size: 8pt; text-align: center; color: #666;\">\n            <t t-if=\"company.partner_id.bank_ids\">\n                <strong>Bank Details:</strong><br/>\n                <t t-foreach=\"company.partner_id.bank_ids[:1]\" t-as=\"bank\">\n                    <span t-field=\"bank.bank_id.name\"/> - <span t-field=\"bank.acc_number\"/>\n                </t>\n            </t>\n        </div>\n    </div>\n</t>"}',
    true
);

-- Insert the report template
INSERT INTO ir_ui_view (name, type, key, arch_db, active) VALUES (
    'VPA Report Template 3',
    'qweb',
    'vpa_document_layout.report_template_3',
    '{"en_US": "<t t-name=\"vpa_document_layout.report_template_3\">\n    <t t-call=\"web.html_container\">\n        <t t-foreach=\"docs\" t-as=\"o\">\n            <t t-call=\"vpa_document_layout.external_layout_vpa_template_3\">\n                <div class=\"page\">\n                    <t t-call=\"sale.report_saleorder_document\"/>\n                </div>\n            </t>\n        </t>\n    </t>\n</t>"}',
    true
);

SELECT 'Templates inserted successfully!';
SQL
