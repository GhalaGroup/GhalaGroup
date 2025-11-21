# -*- coding: utf-8 -*-
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @property
    def procurement_group_id(self):
        """
        Dummy property for compatibility with Manufacturing Order automations.

        This property prevents AttributeError when automations try to access
        procurement_group_id field without checking if sale_stock module is installed.

        Returns:
            False: Always returns False since the real field doesn't exist

        Note:
            The real procurement_group_id field is added by the sale_stock module.
            This dummy property allows automations to check the field without crashing.
        """
        return False
