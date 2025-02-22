# Copyright © 2023 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/15.0/legal/licenses.html).

from odoo import _, api, fields, models
from odoo.tools import float_round
from odoo.exceptions import UserError


class PrintProductLabelTemplate(models.Model):
    _name = "print.product.label.template"
    _description = 'Product Label Templates'
    _order = 'sequence'

    sequence = fields.Integer(default=100)
    name = fields.Char(required=True)
    section_ids = fields.One2many(
        comodel_name='print.product.label.section',
        inverse_name='template_id',
        string='Sections',
    )
    section_count = fields.Integer(compute='_compute_section_count')
    paperformat_id = fields.Many2one(
        comodel_name='report.paperformat',
        # All label paperformats should have prefix "Label: "
        domain="[('name', 'like', 'Label: %')]",
        readonly=True,
        required=True,
    )
    format = fields.Selection(related='paperformat_id.format', store=True)
    orientation = fields.Selection(
        related='paperformat_id.orientation',
        readonly=False,
        required=True,
        help='Page Orientation. Only system administrators can change this value.',
    )
    rows = fields.Integer(default=1, required=True)
    cols = fields.Integer(default=1, required=True)
    margin_top = fields.Float(
        related='paperformat_id.margin_top',
        help='Page Top Margin in mm. Only system administrators can change this value.',
        readonly=False,
    )
    margin_bottom = fields.Float(
        related='paperformat_id.margin_bottom',
        help='Page Bottom Margin in mm. '
             'Only system administrators can change this value.',
        readonly=False,
    )
    margin_left = fields.Float(
        related='paperformat_id.margin_left',
        help='Page Left Margin in mm. Only system administrators can change this value.',
        readonly=False,
    )
    margin_right = fields.Float(
        related='paperformat_id.margin_right',
        help='Page Right Margin in mm. '
             'Only system administrators can change this value.',
        readonly=False,
    )
    padding_top = fields.Float(
        default=0, digits=(10, 2), help='Label Right Padding in mm.')
    padding_bottom = fields.Float(
        default=0, digits=(10, 2), help='Label Bottom Padding in mm.')
    padding_left = fields.Float(
        default=0, digits=(10, 2), help='Label Left Padding in mm.')
    padding_right = fields.Float(
        default=0, digits=(10, 2), help='Label Right Padding in mm.')
    label_style = fields.Char(string='Custom Label Style')
    width = fields.Float(digits=(10, 2), help='Label Width in mm.')
    height = fields.Float(digits=(10, 2), help='Label Height in mm.')
    row_gap = fields.Float(
        string='Horizontal',
        digits=(10, 2),
        default=0,
        help='Horizontal gap between labels, in mm.',
    )
    col_gap = fields.Float(
        string='Vertical',
        digits=(10, 2),
        default=0,
        help='Vertical gap between labels, in mm.',
    )
    is_oversized = fields.Boolean(compute='_compute_is_oversized')
    description = fields.Char()
    preview = fields.Boolean(default=True)
    preview_html = fields.Html(compute='_compute_preview_html', compute_sudo=True)
    ratio_px_in_mm = fields.Float(
        string='Ratio (px in mm)',
        digits=(10, 4),
        compute='_compute_ratio_px_in_mm',
        help="Technical field that indicates how many pixels in 1 mm.",
        store=True,
    )
    active = fields.Boolean(default=True)

    @api.depends('section_ids')
    def _compute_section_count(self):
        for template in self:
            template.section_count = len(template.section_ids)

    @api.depends('width', 'height', 'section_ids', 'section_ids.height')
    def _compute_is_oversized(self):
        for template in self:
            total_height = sum(template.section_ids.mapped('height')) \
                + template.padding_top + template.padding_bottom
            template.is_oversized = template.height < total_height

    @api.depends('paperformat_id', 'paperformat_id.dpi')
    def _compute_ratio_px_in_mm(self):
        for template in self:
            template.ratio_px_in_mm = template.paperformat_id.dpi / 25.4

    def _set_paperformat(self):
        self.ensure_one()
        self.env.ref(
            'garazd_product_label.action_report_product_label_from_template'
        ).sudo().paperformat_id = self.paperformat_id.id

    def write(self, vals):
        """If the Dymo label width or height were changed,
        we should change it to the related paperformat."""
        res = super(PrintProductLabelTemplate, self).write(vals)
        if 'width' in vals or 'height' in vals:
            for template in self:
                if template.paperformat_id.format == 'custom' \
                        and template.cols == 1 and template.rows == 1:
                    template.paperformat_id.sudo().write({
                        # flake8: noqa: E501
                        'page_width': float_round(template.width, precision_rounding=1, rounding_method='UP'),
                        'page_height': float_round(template.height, precision_rounding=1, rounding_method='UP'),
                    })
        return res

    def unlink(self):
        paperformats = self.mapped('paperformat_id')
        res = super(PrintProductLabelTemplate, self).unlink()
        paperformats.sudo().unlink()
        return res

    def get_demo_product_label(self):
        self.ensure_one()
        demo_product = self.env.company.print_label_preview_product_id
        if not demo_product:
            raise UserError(_("Please select a demo product in the General Settings."))

        pricelist_id = self._context.get('pricelist_id')
        pricelist = self.env['product.pricelist'].browse(pricelist_id) \
            if pricelist_id else self.env.company.print_label_preview_pricelist_id

        sale_pricelist_id = self._context.get('sale_pricelist_id')
        sale_pricelist = self.env['product.pricelist'].browse(sale_pricelist_id) \
            if sale_pricelist_id else self.env.company.print_label_preview_sale_pricelist_id

        wizard = self.env['print.product.label'].create({
            'company_id': self.env.company.id,
            'pricelist_id': pricelist.id,
            'sale_pricelist_id': sale_pricelist.id,
        })
        return self.env['print.product.label.line'].create({
            'wizard_id': wizard.id,
            'product_id': demo_product.id,
            'price': demo_product.lst_price,
            'barcode': demo_product.barcode,
        })

    @api.depends('preview')
    def _compute_preview_html(self):
        demo_product = self.env.company.print_label_preview_product_id
        for template in self:
            template.preview_html = template.get_preview_html() if demo_product else ''

    def get_preview_html(self):
        self.ensure_one()
        return self.env['ir.ui.view']._render_template(
            'garazd_product_label_pro.label_preview',
            {
                'back_style': 'background-color: #CCCCCC; '
                              'width: 100%; height: 100%; '
                              'padding: 15px; overflow: hidden;',
                'label_style':
                    'width: %(width)fmm; '
                    'height: %(height)fmm; '
                    'background-color: #FFFFFF; '
                    'margin: auto; '
                    'padding: %(padding_top)fmm '
                    '%(padding_right)fmm '
                    '%(padding_bottom)fmm '
                    '%(padding_left)fmm; '
                    '%(label_custom_style)s' % {
                        'width': self.width,
                        'height': self.height,
                        'padding_top': self.padding_top,
                        'padding_right': self.padding_right,
                        'padding_bottom': self.padding_bottom,
                        'padding_left': self.padding_left,
                        'label_custom_style': self.label_style or '',
                    },
                'sections': self.section_ids.filtered('active'),
                'label': self.get_demo_product_label(),
                'editable_section_id': self._context.get('editable_section_id', False),
            },
        )
