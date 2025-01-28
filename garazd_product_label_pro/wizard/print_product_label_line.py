# Copyright © 2022 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/15.0/legal/licenses.html).

from odoo import api, fields, models


class PrintProductLabelLine(models.TransientModel):
    _inherit = "print.product.label.line"

    price = fields.Float(
        digits='Products Price',
        compute='_compute_product_price',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        compute='_compute_product_price',
    )

    @api.depends('product_id', 'wizard_id.pricelist_id')
    def _compute_product_price(self):
        # When we add a new line by UI in the wizard form, the line doesn't
        # have a product. So we calculate prices only for lines with products
        with_product = self.filtered('product_id')
        for line in with_product:
            # flake8: noqa: E501
            pricelist = line.wizard_id.pricelist_id
            line.price = pricelist._get_product_price(line.product_id, 1.0) if pricelist else line.product_id.lst_price
            line.currency_id = pricelist.currency_id.id if pricelist else line.product_id.currency_id.id
        (self - with_product).price = False
        (self - with_product).currency_id = False
