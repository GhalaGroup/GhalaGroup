# Copyright © 2022 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PrintProductLabelTemplateAdd(models.TransientModel):
    _name = "print.product.label.template.add"
    _description = 'Wizard to add a new product label templates'

    width = fields.Integer(help='Label Width in mm.', required=True)
    height = fields.Integer(help='Label Height in mm.', required=True)
    rows = fields.Integer(default=1, required=True)
    cols = fields.Integer(default=1, required=True)
    paper_format = fields.Selection(
        selection=[
            ('custom', 'Custom'),
            ('A4', 'A4'),
            ('Letter', 'US Letter'),
        ],
        help="Select Proper Paper size",
        default='custom',
        required=True,
    )
    orientation = fields.Selection(
        selection=[
            ('Portrait', 'Portrait'),
            ('Landscape', 'Landscape'),
        ],
        default='Portrait',
        required=True,
    )
    page_width = fields.Integer(help='Page Width in mm.')
    page_height = fields.Integer(help='Page Height in mm.')

    @api.constrains('rows', 'cols', 'width', 'height')
    def _check_page_layout(self):
        for wizard in self:
            if not (wizard.width and wizard.height):
                raise ValidationError(_('The label sizes must be set.'))
            if not (wizard.cols and wizard.rows):
                raise ValidationError(
                    _('The page layout values "Cols" and "Rows" must be set.'))
            if wizard.paper_format == 'custom' and wizard._is_multi_layout():
                if not (self.page_width or self.page_height):
                    raise ValidationError(
                        _('The page sizes "Page Width" and "Page Height" must be set.'))
                if self.page_width < self.width:
                    raise ValidationError(
                        _('The page width must be not less than label width.'))
                if self.page_height < self.height:
                    raise ValidationError(
                        _('The page height must be not less than label height.'))

    def _is_multi_layout(self):
        self.ensure_one()
        return self.cols > 1 or self.rows > 1

    def _get_label_name(self):
        self.ensure_one()
        # flake8: noqa: E501
        paperformat_name = 'Custom' if self.paper_format == 'custom' else self.paper_format
        page_sizes = f" {self.page_width}x{self.page_height} mm" if self.page_width and self.page_height else ""
        layout_name = f" ({paperformat_name}{page_sizes}: {self.cols * self.rows} pcs, {self.cols}x{self.rows})" if self.paper_format != "custom" or self._is_multi_layout() else ""
        return f'Label: {self.width}x{self.height} mm{layout_name}'

    def _create_paperformat(self):
        self.ensure_one()
        return self.env['report.paperformat'].sudo().create({
            'name': self._get_label_name(),
            'format': self.paper_format,
            'page_width': 0 if self.paper_format != 'custom'
            else self.page_width if self._is_multi_layout()
            else self.width,
            'page_height': 0 if self.paper_format != 'custom'
            else self.page_height if self._is_multi_layout()
            else self.height,
            'orientation': self.orientation,
            'margin_top': 0,
            'margin_bottom': 0,
            'margin_left': 0,
            'margin_right': 0,
            'header_spacing': 0,
            'header_line': False,
            'disable_shrinking': True,
            'dpi': 96,
            'default': False,
        })

    def action_create(self):
        self.ensure_one()
        template = self.env['print.product.label.template'].create({
            'name': self._get_label_name().replace(':', '', 1),
            'paperformat_id': self._create_paperformat().id,
            'width': self.width,
            'height': self.height,
            'rows': self.rows,
            'cols': self.cols,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': template._name,
            'res_id': template.id,
            'view_mode': 'form',
        }
