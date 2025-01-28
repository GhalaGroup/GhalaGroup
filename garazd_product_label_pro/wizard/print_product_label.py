# Copyright © 2023 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/15.0/legal/licenses.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PrintProductLabel(models.TransientModel):
    _inherit = "print.product.label"

    report_id = fields.Many2one(
        default=lambda self: self.env.ref(
            'garazd_product_label.action_report_product_label_from_template'),
    )
    template_id = fields.Many2one(
        comodel_name='print.product.label.template',
        # flake8: noqa: E501
        default=lambda self: self.env.user.print_label_template_id or self.env['print.product.label.template'].search([], limit=1),
    )
    template_preview_html = fields.Html(
        compute='_compute_template_preview_html',
        compute_sudo=True,
    )
    label_template_preview = fields.Boolean(help='Show Label Template Sample.')
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
    )
    sale_pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Sales Pricelist',
        help='Specify this second pricelist to put one more product price to a label.',
    )
    skip_place_count = fields.Integer(
        string='Skip Places',
        default=0,
        help='Specify how many places for labels should be skipped on printing. This can'
             ' be useful if you are printing on a sheet with labels already printed.',
    )

    @api.depends('template_id', 'pricelist_id', 'sale_pricelist_id', 'lang')
    def _compute_template_preview_html(self):
        for wizard in self:
            wizard.template_preview_html = wizard.with_context(**{
                'preview_mode': True,
                'pricelist_id': wizard.pricelist_id.id,
                'sale_pricelist_id': wizard.sale_pricelist_id.id,
                'lang': wizard.lang or self._context.get('lang'),
            }).template_id.preview_html

    def _get_label_data(self):
        self.ensure_one()
        labels = self.get_labels_to_print()
        if not self.is_template_report:
            return {'ids': labels.ids, 'data': {}}
        if not self.template_id:
            raise UserError(_('Select the label template to print.'))
        self.template_id._set_paperformat()
        label_data = {
            'ids': labels.ids,
            'data': {
                'rows': self.template_id.rows,
                'cols': self.template_id.cols,
                'row_gap': self.template_id.row_gap,
                'col_gap': self.template_id.col_gap,
                'label_style':
                    'overflow: hidden;'
                    'font-family: "Arial";'
                    'width: %(width).2fmm;'
                    'height: %(height).2fmm;'
                    'padding: %(padding_top).2fmm %(padding_right).2fmm'
                    ' %(padding_bottom).2fmm %(padding_left).2fmm;'
                    'border: %(border)s;'
                    '%(custom_style)s' % {
                        'width': self.template_id.width,
                        'height': self.template_id.height,
                        'padding_top': self.template_id.padding_top,
                        'padding_right': self.template_id.padding_right,
                        'padding_bottom': self.template_id.padding_bottom,
                        'padding_left': self.template_id.padding_left,
                        'border': "%dpx solid #EEE" % self.border_width
                        if self.border_width else 0,
                        'custom_style': self.template_id.label_style or '',
                    },
                'skip_places': self.skip_place_count,
            },
        }
        # Add extra styles for multi labels
        if self.template_id.cols != 1 or self.template_id.rows != 1:
            label_data['data']['label_style'] += 'float: left;'
        return label_data

    def _get_report_action_params(self):
        ids, data = super(PrintProductLabel, self)._get_report_action_params()
        if self.is_template_report:
            ids = None
            data = self._get_label_data()
        return ids, data

    def action_add_template(self):
        self.ensure_one()
        return {
            'name': _('Add a New Label Template'),
            'type': 'ir.actions.act_window',
            'res_model': 'print.product.label.template.add',
            'view_mode': 'form',
            'target': 'new',
        }

    def action_edit_template(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.template_id._name,
            'res_id': self.template_id.id,
            'view_mode': 'form',
        }

    def action_reset_skip(self):
        """Reset the skip empty places count value. """
        self.ensure_one()
        self.write({'skip_place_count': 0})
