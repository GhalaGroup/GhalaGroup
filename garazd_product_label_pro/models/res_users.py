from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    print_label_template_id = fields.Many2one(
        comodel_name='print.product.label.template',
        string='Default Template',
    )
