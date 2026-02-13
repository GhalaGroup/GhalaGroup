# -*- coding: utf-8 -*-
import json
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _prepare_mo_vals(self, product_id, product_qty, product_uom, location_id,
                         name, origin, company_id, values, bom):
        """Override to inject dimension data from SO procurement into MO."""
        mo_vals = super()._prepare_mo_vals(
            product_id, product_qty, product_uom, location_id,
            name, origin, company_id, values, bom,
        )

        # Check top-level first, then nested procurement_values
        # (when route goes through a pull rule, values are serialized into
        # stock.move.procurement_values and nested under 'procurement_values' key)
        vpa_data = values.get('vpa_dimension_data')
        if not vpa_data:
            pv = values.get('procurement_values')
            if isinstance(pv, dict):
                vpa_data = pv.get('vpa_dimension_data')
        # Fallback: read directly from SO line if sale_line_id is available
        if not vpa_data:
            sol_id = values.get('sale_line_id')
            if not sol_id:
                pv = values.get('procurement_values')
                if isinstance(pv, dict):
                    sol_id = pv.get('sale_line_id')
            if sol_id:
                if isinstance(sol_id, int):
                    sale_line = self.env['sale.order.line'].browse(sol_id)
                else:
                    sale_line = sol_id  # already a recordset
                if sale_line.exists() and sale_line.dimension_data_json:
                    vpa_data = sale_line.dimension_data_json

        if vpa_data:
            try:
                data = json.loads(vpa_data)
                mo_vals['dimension_template_id'] = data.get('template_id')
                mo_vals['dimension_data_json'] = vpa_data
                mo_vals['computed_dimension_qty'] = data.get('computed_qty', 0)
                mo_vals['dimension_unit_count'] = int(data.get('unit_count', 1))
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                _logger.error("VPA _prepare_mo_vals: failed to parse dimension data: %s", e)

        return mo_vals
