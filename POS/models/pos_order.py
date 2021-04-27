from odoo import api, fields, models

class POS(models.Model):
    _inherit = "pos.order"

    d = {}
    def _payment_fields(self, order, ui_paymentline):
       res = super(POS, self)._payment_fields(order,ui_paymentline)
       something = ui_paymentline['note']
       POS.d.update({'note':something})
       return res

    def create(self, values):

        v = super(POS, self).create(values)
        POS.d = v

        return v


