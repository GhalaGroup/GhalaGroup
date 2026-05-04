# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import models, fields
from odoo.exceptions import UserError
from datetime import date
from datetime import datetime


class UpdateEffective(models.Model):
    """Extends stock.picking to allow changing effective dates with automatic synchronization."""

    _inherit = "stock.picking"

    date_of_transfer = fields.Datetime(
        string="Effective Date",
        default=False,
        help="Set a custom effective date before validation. Leave empty to use current date/time."
    )

    def wiz_open(self):
        """Opens the wizard to change effective date after validation."""
        return {
            'name': 'Change Effective Date',
            'type': 'ir.actions.act_window',
            'res_model': 'change.effective.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    def button_validate(self):
        """
        Override the validate button to add custom effective date functionality.
        This allows setting a specific effective date instead of using the current date/time.
        """
        res = super(UpdateEffective, self).button_validate()

        # If transfer date is empty, skip custom date logic
        # and use Odoo's default calculation (current date/time)
        if self.date_of_transfer != False:
            # Check if stock_valuation_layer table exists
            self.env.cr.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'stock_valuation_layer'
                )
            """)
            has_valuation_layer = self.env.cr.fetchone()[0]

            # Check if account_move table exists
            self.env.cr.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'account_move'
                )
            """)
            has_accounting = self.env.cr.fetchone()[0]

            # Update the date_done (Effective Date) field
            if self.date_of_transfer != False:
                selected_date = self.date_of_transfer
            else:
                selected_date = datetime.now()

            self.date_done = selected_date

            # Update stock valuation layer dates (only if table exists)
            if has_valuation_layer:
                self.env.cr.execute("UPDATE stock_valuation_layer SET create_date = (%s) WHERE description LIKE (%s)", [selected_date, str(self.name + "%")])

            # Update stock move line dates
            for stock_move_line in self.env['stock.move.line'].search([('reference', 'ilike', str(self.name + "%"))]):
                stock_move_line.date = selected_date

            # Update stock move dates
            for stock_move in self.env['stock.move'].search([('reference', 'ilike', str(self.name + "%"))]):
                stock_move.date = selected_date

            # Update account move line dates
            if has_accounting:
                self.env.cr.execute("UPDATE account_move_line SET date = (%s) WHERE ref SIMILAR TO %s", [selected_date, str(self.name + "%")])

            # Update account move dates
            if has_accounting:
                self.env.cr.execute("UPDATE account_move set date = (%s) WHERE ref SIMILAR TO %s", [selected_date, str(self.name + "%")])

            # Get system default currency ID
            system_default_currency = int(self.env.ref('base.main_company').currency_id)
            current_picking_id = self.picking_type_id.code
            purchase_orders_ids = self.env['purchase.order'].search([('name', '=', str(self.origin))])

            # If this is an incoming transfer from a Purchase Order using foreign currency,
            # recalculate the valuation with the correct exchange rate for the selected date
            if current_picking_id == 'internal':
                pass
            elif current_picking_id == 'outgoing':
                pass
            elif current_picking_id == 'incoming':
                if purchase_orders_ids and purchase_orders_ids.currency_id and purchase_orders_ids.currency_id.id != system_default_currency:
                    company = self.env.company
                    po_currency = purchase_orders_ids.currency_id
                    rate = po_currency._get_conversion_rate(po_currency, company.currency_id, company, selected_date)

                    if not rate:
                        raise UserError('You have selected the currency rate of ' + str(po_currency.name) + ' which is currently not available based on your selected date. Make sure to fill it under Accounting > Settings > Currencies > ' + str(po_currency.name) + '!')
                    else:
                        po_quantity = []
                        po_price_unit = []
                        po_tax_include = []
                        po_tax_amount = []
                        po_subtotal = []

                        for product in self.env['purchase.order.line'].search([('order_id', '=', int(purchase_orders_ids))]):
                            po_quantity.append(product.product_qty)
                            po_price_unit.append(product.price_unit)
                            po_tax_include.append(product.tax_ids.price_include)
                            po_tax_amount.append(product.price_tax)
                            po_subtotal.append(product.price_subtotal)

                        price_unit = []
                        counter = 0
                        for id in po_quantity:
                            if po_tax_include[counter] == True:
                                unit_value = (float(po_quantity[counter]) * float(po_price_unit[counter]) - float(po_tax_amount[counter])) * float(rate)
                                price_unit.append(float(unit_value))
                            else:
                                unit_value = float(rate) * float(po_price_unit[counter]) * po_quantity[counter]
                                price_unit.append(float(unit_value))
                            counter += 1

                        # Calculate stock valuation layer values with new exchange rate
                        if has_valuation_layer:
                            counter = 0
                            for product in self.env['stock.valuation.layer'].search([('description', 'ilike', str(self.name + "%"))]):
                                product.unit_cost = price_unit[counter] / product.quantity
                                product.value = product.unit_cost * product.quantity
                                product.remaining_value = product.remaining_qty * (price_unit[counter] / product.quantity)
                                counter += 1

                        # Calculate account move values with new exchange rate
                        account_move_ids = []
                        account_move_search = self.env['account.move'].search([('ref', 'like', str(self.name + "%"))])
                        for item in account_move_search:
                            account_move_ids.append((int(item.id)))

                        journal_entry = sorted(account_move_ids)

                        account_move_line = []
                        debit = []
                        credit = []

                        for journal_id in journal_entry:
                            for item in self.env['account.move.line'].search([('move_id', '=', journal_id)]):
                                account_move_line.append(int(item.id))
                                debit.append(int(item.debit))
                                credit.append(int(item.credit))

                        account_move_lines = [account_move_line[i:i + 2] for i in range(0, len(account_move_line), 2)]

                        counter = 0
                        for record in account_move_lines:
                            debit = float(abs(price_unit[counter]))
                            self.env['account.move.line'].search([('id', '=', int(record[1]))]).with_context(check_move_validity=False).write({'debit': debit})

                            credit = float(abs(price_unit[counter]))
                            self.env['account.move.line'].search([('id', '=', int(record[0]))]).with_context(check_move_validity=False).write({'credit': credit})

                            counter += 1

                        # Update product cost in master product data
                        if has_valuation_layer:
                            for product in self.move_ids_without_package:
                                if product.product_tmpl_id.categ_id.property_cost_method == 'average':
                                    # For Average costing method, recalculate average cost
                                    valuations = self.env['stock.valuation.layer'].search([('product_id', '=', product.product_id.id)])
                                    sum = 0
                                    qty = 0
                                    for valuation in valuations:
                                        sum += valuation.value
                                        qty += valuation.quantity

                                        standard_price = sum / qty
                                        res_id = 'product.product,' + str(product.product_id.id)

                                        # Update the standard price property
                                        ir_property_standard = self.env['ir.property'].sudo().search([('res_id', '=', res_id), ('name', '=', 'standard_price')])
                                        ir_property_standard.value_float = standard_price

                                elif product.product_tmpl_id.categ_id.property_cost_method == 'fifo':
                                    # For FIFO costing method, use the unit cost from valuation layer
                                    valuation = self.env['stock.valuation.layer'].search([('product_id', '=', product.product_id.id)])
                                    if len(valuation) == 1:
                                        res_id = 'product.product,' + str(product.product_id.id)
                                        self.env.cr.execute("UPDATE ir_property SET value_float = (%s) WHERE res_id = (%s)", [valuation.unit_cost, res_id])
            else:
                pass

                def update_journal_name(selected_prefix, picking_name):
                    """Update journal entry names with new sequence based on selected date."""
                    already_created_sequence_prefix = self.env['account.move'].search([('sequence_prefix', '=', str(selected_prefix))])
                    seq_numbers = [account_move.sequence_number for account_move in already_created_sequence_prefix]
                    max_sequence_number = max(seq_numbers, default=0) + 1

                    for journal_entries in self.env['account.move'].search([('ref', 'like', picking_name)]):
                        new_name = selected_prefix + str(max_sequence_number).zfill(4)
                        self.env.cr.execute("UPDATE account_move SET name = (%s) WHERE id = %s", [new_name, int(journal_entries.id)])
                        journal_entries.sequence_number = max_sequence_number
                        journal_entries.sequence_prefix = selected_prefix

                        for invoice_line_ids in journal_entries.invoice_line_ids:
                            invoice_line_ids.move_name = new_name

                        max_sequence_number += 1

                # Get journal name and determine year/month from selected date
                account_move = self.env['account.move'].search([('ref', 'ilike', str(self.name))])
                account_move_short_code = account_move.journal_id.code or self.env["account.journal"].search([('name', '=', 'Inventory Valuation')]).code
                selected_year = selected_date.strftime("%Y")
                selected_month = selected_date.strftime("%m")

                currentMonth = datetime.now().month
                currentYear = datetime.now().year

                # If selected month and year are the same as current month and year, skip renaming
                # This avoids conflicts with the accounting sequence system
                # Backdating is only allowed for dates in different months than the current month
                if int(selected_month) == currentMonth and int(selected_year) == currentYear:
                    pass
                else:
                    if account_move_short_code != False:
                        # Form new journal entry name with selected date
                        selected_prefix = str(account_move_short_code + "/" + selected_year + "/" + selected_month + "/")
                        collected_name = []  # Cache query results for performance
                        for created_journals in self.env['account.move'].search([('name', 'like', str(selected_prefix))]):
                            collected_name.append(created_journals.name)

                        picking_name = str(self.name)
                        if selected_year == date.today().year and selected_month == date.today().month:
                            pass
                        else:
                            update_journal_name(selected_prefix, picking_name)
                    else:
                        pass
        else:
            pass

        return res