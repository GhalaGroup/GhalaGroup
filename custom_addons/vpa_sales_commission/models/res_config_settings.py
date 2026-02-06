# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    commission_production_enabled = fields.Boolean(
        string='Enable Production Commission',
        config_parameter='vpa_sales_commission.production_enabled',
        default=True,
        help='Enable commission calculation based on Manufacturing Orders',
    )
    commission_sales_enabled = fields.Boolean(
        string='Enable Sales Commission',
        config_parameter='vpa_sales_commission.sales_enabled',
        default=False,
        help='Enable commission calculation based on Sales Orders (Phase 2)',
    )
    commission_auto_create = fields.Boolean(
        string='Auto-create Commission on MO Done',
        config_parameter='vpa_sales_commission.auto_create',
        default=True,
        help='Automatically create commission lines when Manufacturing Orders are completed',
    )

    # Commission Payment Accounts
    commission_journal_id = fields.Many2one(
        'account.journal',
        string='Commission Journal',
        domain="[('type', '=', 'general')]",
        help='Default journal for commission payment entries',
    )
    commission_production_expense_account_id = fields.Many2one(
        'account.account',
        string='Production Commission Expense Account',
        help='Default debit account for production commission payments',
    )
    commission_production_payable_account_id = fields.Many2one(
        'account.account',
        string='Production Commission Payable Account',
        help='Default credit account for production commission payments',
    )
    commission_sales_expense_account_id = fields.Many2one(
        'account.account',
        string='Sales Commission Expense Account',
        help='Default debit account for sales commission payments',
    )
    commission_sales_payable_account_id = fields.Many2one(
        'account.account',
        string='Sales Commission Payable Account',
        help='Default credit account for sales commission payments',
    )

    def set_values(self):
        super().set_values()
        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_param('vpa_sales_commission.journal_id',
                       str(self.commission_journal_id.id) if self.commission_journal_id else '')
        ICP.set_param('vpa_sales_commission.production_expense_account_id',
                       str(self.commission_production_expense_account_id.id) if self.commission_production_expense_account_id else '')
        ICP.set_param('vpa_sales_commission.production_payable_account_id',
                       str(self.commission_production_payable_account_id.id) if self.commission_production_payable_account_id else '')
        ICP.set_param('vpa_sales_commission.sales_expense_account_id',
                       str(self.commission_sales_expense_account_id.id) if self.commission_sales_expense_account_id else '')
        ICP.set_param('vpa_sales_commission.sales_payable_account_id',
                       str(self.commission_sales_payable_account_id.id) if self.commission_sales_payable_account_id else '')

    @api.model
    def get_values(self):
        res = super().get_values()
        ICP = self.env['ir.config_parameter'].sudo()

        journal_id = ICP.get_param('vpa_sales_commission.journal_id', '')
        prod_expense_id = ICP.get_param('vpa_sales_commission.production_expense_account_id', '')
        prod_payable_id = ICP.get_param('vpa_sales_commission.production_payable_account_id', '')
        sales_expense_id = ICP.get_param('vpa_sales_commission.sales_expense_account_id', '')
        sales_payable_id = ICP.get_param('vpa_sales_commission.sales_payable_account_id', '')

        res.update(
            commission_journal_id=int(journal_id) if journal_id else False,
            commission_production_expense_account_id=int(prod_expense_id) if prod_expense_id else False,
            commission_production_payable_account_id=int(prod_payable_id) if prod_payable_id else False,
            commission_sales_expense_account_id=int(sales_expense_id) if sales_expense_id else False,
            commission_sales_payable_account_id=int(sales_payable_id) if sales_payable_id else False,
        )
        return res
