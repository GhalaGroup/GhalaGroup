from odoo import  models
from datetime import datetime

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    dd = {}
    # def create(self, values):
    #
    #     v = super(SaleOrder, self).create(values)
    #     print('')
    #     order_lines = values.get('order_line')
    #     # for product in order_lines:
    #     #     print('product:',product.id)
    #     product_id = dictt['product_id']
    #     # print('list price',product_id.list_price)
    #     # print('lst price',product_id.lst_price)
    # #     print("order line", order_lines[0][2])
    # #     print('product:', dictt['product_id'])
    # #     d = [[0 ,False,{'product_id':dictt['product_id'], 'name':dictt['name'],'price_unit':dictt['price_unit'],
    # #                     'product_uom_qty':dictt['product_uom_qty']}]]
    # #     self.dd = d
    # #     saleOrder = self.env['purchase.order'].create({'partner_id' : 1,'order_line':d})
    # #     print(saleOrder)
    #     return v

    def _action_confirm(self):
        res = super(SaleOrder, self)._action_confirm()
        partnerRef = ''
        lines = []
        # print(self.name)
        partnerRef = self.name
        for x in self.order_line:
            # print('id', x.product_id.id)
            # print('name', x.name)
            # print('price', x.product_id.standard_price)
            # print('qty', x.product_uom_qty)
            # print('lst variant price', x.product_id.lst_price)
            # print('lisst template price', x.product_id.list_price)
            # the product id it takes is the product.product
            lines.append([0, False, {'product_id':10827, 'name': 'Ecommerce Sales Service' +' - ' + self.name +' - ' + x.name, 'price_unit': x.price_unit - x.product_id.standard_price,
                             'product_uom_qty': x.product_uom_qty, 'product_qty': x.product_uom_qty}])
        x = self.order_line
        # print(self.company_id.id)
        print(lines)
        if self.website_id and x and self.company_id.id == 1 :
            purchaseOrder = self.env['purchase.order'].create({'partner_id': 4,'order_line': lines, 'partner_ref' : partnerRef })
            print('this is res model id',purchaseOrder.id)
            activity = self.env['mail.activity'].create({'res_model_id': self.env['ir.model']._get(self.env['purchase.order']._name).id, 'res_id': purchaseOrder.id, 'recommended_activity_type_id': False, 'activity_type_id': 4, 'summary': purchaseOrder.name, 'date_deadline': datetime.today().strftime('%Y-%m-%d'), 'user_id': 2, 'note': purchaseOrder.name}
)
            print(purchaseOrder)
            purchaseOrder.button_confirm()
        return res
