from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    print_label_preview_product_id = fields.Many2one(
        string='Demo Product',
        related='company_id.print_label_preview_product_id',
        readonly=False,
    )
    print_label_preview_pricelist_id = fields.Many2one(
        string='Demo Pricelist',
        related='company_id.print_label_preview_pricelist_id',
        readonly=False,
    )
    print_label_preview_sale_pricelist_id = fields.Many2one(
        string='Demo Promo Pricelist',
        related='company_id.print_label_preview_sale_pricelist_id',
        readonly=False,
    )
