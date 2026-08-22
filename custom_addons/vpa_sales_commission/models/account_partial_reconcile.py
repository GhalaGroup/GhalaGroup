# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, models


class AccountPartialReconcile(models.Model):
    """Reverse mirror of the commission <-> accounting sync.

    The allocation model pushes commission data DOWN into accounting
    (matches between payments and the year's bills). These hooks close the
    loop in the other direction: when an accountant manually reconciles or
    unreconciles a commission payment against a commission bill, the
    commission allocations follow, so the two layers can never disagree —
    whichever door the user goes through.

    Skipped when:
    - _vpa_commission_sync: the change is our own sync writing accounting;
      mirroring it back would recurse.
    - _vpa_commission_lifecycle: a document lifecycle operation (reset to
      draft) tears down ALL matches temporarily; commission applications
      must survive it, and the _post hook rebuilds the matches from them.
    """
    _inherit = 'account.partial.reconcile'

    def _vpa_commission_targets(self):
        """(payment, year, amount_pc) for each partial in ``self`` that links
        an outbound payment's payable line to a commission bill's payable
        line. amount_pc is the matched amount in the payment currency."""
        targets = []
        for partial in self:
            debit, credit = partial.debit_move_id, partial.credit_move_id
            # An outbound payment debits payable, a vendor bill credits it.
            payment = debit.move_id.origin_payment_id
            year = credit.move_id.commission_year_id
            if (payment and year
                    and payment.payment_type == 'outbound'
                    and credit.move_id.move_type == 'in_invoice'
                    and debit.account_id.account_type == 'liability_payable'):
                targets.append((payment, year, partial.debit_amount_currency))
        return targets

    def _vpa_skip_commission_mirror(self):
        return bool(self.env.context.get('_vpa_commission_sync')
                    or self.env.context.get('_vpa_commission_lifecycle'))

    @api.model_create_multi
    def create(self, vals_list):
        partials = super().create(vals_list)
        if not self._vpa_skip_commission_mirror():
            Allocation = self.env['vpa.commission.payment.allocation'].sudo()
            for payment, year, amount_pc in partials._vpa_commission_targets():
                Allocation._follow_manual_reconcile(payment, year, amount_pc)
        return partials

    def unlink(self):
        targets = ([] if self._vpa_skip_commission_mirror()
                   else self._vpa_commission_targets())
        res = super().unlink()
        if targets:
            Allocation = self.env['vpa.commission.payment.allocation'].sudo()
            for payment, year, amount_pc in targets:
                Allocation._follow_manual_unreconcile(payment, year, amount_pc)
        return res
