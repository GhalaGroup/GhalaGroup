from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    print_label_preview_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Demo Product',
        default=lambda self: self.env['product.product'].search([
            ('barcode', '!=', False)
        ], limit=1),
    )
    print_label_preview_pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Demo Pricelist',
        default=lambda self: self.env['product.pricelist'].search([])[:1],
    )
    print_label_preview_sale_pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Demo Promo Pricelist',
        default=lambda self: self.env['product.pricelist'].search([])[1:2],
    )
