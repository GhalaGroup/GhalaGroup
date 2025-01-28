# Copyright © 2023 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html).

from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestProductLabel(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.label_template_50x25 = cls.env['print.product.label.template'].create({
            'name': 'Test Label',
            'paperformat_id': cls.env.ref('garazd_product_label_pro.paperformat_label_custom_50x25').id,
            'orientation': 'Portrait',
            'cols': 1,
            'rows': 1,
            'width': 50,
            'height': 25,
        })
        cls.product_a = cls.env['product.product'].create({
            'name': 'Test Product A',
            'detailed_type': 'consu',
            'list_price': 20.0,
            'barcode': '1234567890',
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Test Product B',
            'detailed_type': 'consu',
            'list_price': 199.99,
            'barcode': '9999999999999',
        })

    def setUp(self):
        super(TestProductLabel, self).setUp()

        self.print_wizard = self.env['print.product.label'].with_context(**{
            'active_model': 'product.product',
            'default_product_ids': [self.product_a.id, self.product_b.id],
        }).create({})
