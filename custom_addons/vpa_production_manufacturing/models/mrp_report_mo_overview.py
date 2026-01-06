# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, models


class ReportMrpReportMoOverview(models.AbstractModel):
    """Override MO Overview report to handle Master BOM template moves.

    For template moves, both BOM Cost and MO Cost should use master_bom_qty
    (planned qty from Master BOM) instead of move quantities based on placeholder.
    """
    _inherit = 'report.mrp.report_mo_overview'

    def _format_component_move(self, production, move_raw, replenishments, replenish_data, level, index):
        """Override to calculate costs correctly for template moves.

        For template moves:
        - BOM Cost = master_bom_qty × real product's unit price (planned cost)
        - MO Cost = master_bom_qty × real product's unit price (planned cost)
        - Real Cost = actual consumed quantity × real product's unit price

        This allows comparing planned (Master BOM) vs actual costs.
        For regular moves, use standard behavior.
        """
        result = super()._format_component_move(
            production, move_raw, replenishments, replenish_data, level, index
        )

        # Check if this is a template move with master_bom_qty
        if hasattr(move_raw, 'is_template_move') and move_raw.is_template_move:
            if move_raw.master_bom_qty:
                currency = (production.company_id or self.env.company).currency_id

                # Both BOM Cost and MO Cost = master_bom_qty × unit price
                # This shows the planned cost from the Master BOM
                planned_cost = currency.round(
                    self._get_component_real_cost(move_raw, move_raw.master_bom_qty)
                )
                result['bom_cost'] = planned_cost
                result['mo_cost'] = planned_cost

                # Update decorators based on planned cost vs real cost
                if production.state == 'draft':
                    # Draft: compare BOM cost vs MO cost (both same, so no decorator)
                    result['mo_cost_decorator'] = False
                elif production.state == 'done':
                    # Done: MO Cost stays as planned, Real Cost shows actual
                    # Decorator compares MO Cost (planned) vs Real Cost (actual)
                    result['real_cost_decorator'] = self._get_comparison_decorator(
                        planned_cost, result['real_cost'], currency.rounding
                    )
                    result['mo_cost_decorator'] = False
                else:
                    # Confirmed/In Progress: compare planned vs real
                    cost_to_compare = result['real_cost'] if production.state != 'confirmed' else planned_cost
                    result['mo_cost_decorator'] = self._get_comparison_decorator(
                        cost_to_compare, planned_cost, currency.rounding
                    )

        return result
