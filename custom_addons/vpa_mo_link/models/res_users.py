# -*- coding: utf-8 -*-
from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    vpa_mrp_home = fields.Selection(
        [
            ('overview', 'Work Centers Overview'),
            ('mo', 'Manufacturing Orders'),
            ('so', 'Sales Orders'),
            ('other', 'Other Orders'),
        ],
        string='Manufacturing Home',
        default='overview',
        help="The page that opens when you click the Manufacturing app.",
    )

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['vpa_mrp_home']

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ['vpa_mrp_home']
