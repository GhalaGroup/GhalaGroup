# -*- coding: utf-8 -*-
# Copyright (C) 2025 VPA Solutions Limited
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import models, _
from odoo.exceptions import UserError


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    # ------------------------------------------------------------------
    # Inventory adjustment approval gate
    # ------------------------------------------------------------------
    def _set_inventory_quantity(self):
        """Gate the *auto-apply* path (product 'Update Quantity' / inline On-Hand
        edit). That path calls action_apply_inventory() from an inverse and
        DISCARDS the returned action, so a wizard cannot be shown - the change
        would silently vanish. Instead, when approval is required we capture the
        pending changes as requests here and raise a clear message.
        """
        if self.env.context.get('nns_adj_approved'):
            return super()._set_inventory_quantity()

        gated = self.filtered(lambda q: (q.company_id or self.env.company).nns_adj_approval)
        changed = gated.filtered(
            lambda q: q.product_id.uom_id.compare(
                q.inventory_quantity_auto_apply, q.quantity) != 0)
        if not changed:
            return super()._set_inventory_quantity()

        # Skip quants that ALREADY have a pending request for the same
        # product/location/lot. We SILENTLY skip them (no error popup): the grid
        # can re-trigger this inverse on open/refresh, and raising there would
        # spam the user with 'already awaiting approval' just for viewing.
        already = changed.filtered(lambda q: self._nns_has_pending_request(q))
        to_request = changed - already

        # Apply any non-gated quants normally first (their changes are legitimate).
        rest = self - gated
        if rest:
            super(StockQuant, rest)._set_inventory_quantity()

        # Reset the transient counted value on already-pending quants so they
        # return to their displayed on-hand without changing stock or popping up.
        if already:
            already.write({'inventory_quantity_set': False})

        if not to_request:
            # Nothing genuinely new to submit - do nothing, no popup.
            return True

        # The gated changes become approval requests. We must raise to inform the
        # user (the auto-apply caller ignores return values), and a raise rolls
        # back this transaction - so the requests are written on an INDEPENDENT
        # cursor to survive the rollback (same pattern as the block log).
        # Capture the REAL calling user now. The independent cursor below runs as
        # the system user (OdooBot), so we must stamp the request with this uid
        # explicitly - otherwise the requester would wrongly show as OdooBot.
        real_uid = self.env.uid
        payload = [{
            'product_id': q.product_id.id,
            'location_id': q.location_id.id,
            'lot_id': q.lot_id.id or False,
            'package_id': q.package_id.id or False,
            'owner_id': q.owner_id.id or False,
            'counted': q.inventory_quantity_auto_apply,
            'company_id': (q.company_id or self.env.company).id,
        } for q in to_request]
        refs = self._nns_persist_autoapply_requests(payload, real_uid)
        raise UserError(self._nns_adj_submitted_message(refs))

    def _nns_has_pending_request(self, quant):
        """True if a pending adjustment request already exists for this quant's
        product/location/lot/package/owner."""
        return bool(self.env['stock.adjustment.request'].sudo().search_count([
            ('state', '=', 'pending'),
            ('product_id', '=', quant.product_id.id),
            ('location_id', '=', quant.location_id.id),
            ('lot_id', '=', quant.lot_id.id or False),
            ('package_id', '=', quant.package_id.id or False),
            ('owner_id', '=', quant.owner_id.id or False),
        ]))

    def _nns_persist_autoapply_requests(self, payload, real_uid):
        """Create adjustment requests on a fresh cursor so they survive the
        UserError rollback that immediately follows. Records the real requesting
        user (real_uid), not the system user of the independent cursor. Returns a
        list of (name, product_name, current, counted, uom) tuples for the
        message."""
        refs = []
        try:
            with self.pool.cursor() as new_cr:
                # Run the new-cursor env AS the real user so create_uid,
                # requested_by and any tracking all attribute to them.
                new_env = self.env(cr=new_cr, user=real_uid)
                Quant = new_env['stock.quant'].sudo()
                Request = new_env['stock.adjustment.request'].sudo()
                for row in payload:
                    product = new_env['product.product'].browse(row['product_id'])
                    location = new_env['stock.location'].browse(row['location_id'])
                    current = sum(Quant._gather(
                        product, location,
                        lot_id=new_env['stock.lot'].browse(row['lot_id']) or None,
                        package_id=new_env['stock.package'].browse(row['package_id']) or None,
                        owner_id=new_env['res.partner'].browse(row['owner_id']) or None,
                        strict=True).mapped('quantity'))
                    req = Request.create({
                        'product_id': row['product_id'],
                        'location_id': row['location_id'],
                        'lot_id': row['lot_id'],
                        'package_id': row['package_id'],
                        'owner_id': row['owner_id'],
                        'current_qty': current,
                        'counted_qty': row['counted'],
                        'diff_qty': row['counted'] - current,
                        'reason': _('Submitted via Update Quantity'),
                        'requested_by': real_uid,
                        'company_id': row['company_id'],
                    })
                    refs.append((req.name, product.display_name, current,
                                 row['counted'], product.uom_id.name or _('Units')))
                # Commit explicitly so the requests survive the UserError-driven
                # rollback of the caller's transaction that follows immediately.
                new_cr.commit()
        except Exception:  # pragma: no cover - never mask the block with a log error
            refs = refs or [(_('(request)'), '', 0, 0, '')]
        return refs

    def _nns_adj_submitted_message(self, refs):
        lines = [_(
            "This inventory adjustment requires manager approval and has been "
            "submitted as a request. Stock has NOT changed yet.")]
        lines.append("")
        for name, product, current, counted, uom in refs:
            lines.append("  %s  %s: %g -> %g %s" % (name, product, current, counted, uom))
        lines.append("")
        lines.append(_(
            "Track it under Inventory > Operations > Adjustment Approvals."))
        return "\n".join(lines)

    def action_apply_inventory(self, date=None):
        """Intercept the 'Apply' on inventory adjustments. When the company
        requires approval, capture each pending change as an approval request
        instead of changing stock, and stop here. Approved replays carry the
        `nns_adj_approved` context flag and pass straight through.
        """
        if self.env.context.get('nns_adj_approved'):
            return super().action_apply_inventory(date=date)

        gated = self.filtered(lambda q: (q.company_id or self.env.company).nns_adj_approval)
        if not gated:
            return super().action_apply_inventory(date=date)

        # Only quants whose counted quantity actually differs need a request.
        to_request = gated.filtered(
            lambda q: q.inventory_quantity_set and q.product_id.uom_id.compare(
                q.inventory_quantity, q.quantity) != 0)
        if not to_request:
            # Apply any non-gated quants normally.
            rest = self - gated
            return super(StockQuant, rest).action_apply_inventory(date=date) if rest else True

        return self._nns_open_adjustment_wizard(to_request)

    def _nns_open_adjustment_wizard(self, quants):
        return {
            'name': _('Inventory Adjustment - Reason Required'),
            'type': 'ir.actions.act_window',
            'res_model': 'nns.adjustment.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_quant_ids': quants.ids},
        }

    def _nns_build_requests(self, reason):
        """Create one approval request per quant in self. The physical on-hand is
        read from the authoritative quants (summed `quantity`) rather than the
        transient inventory-mode `quant.quantity`, which is not reliable here."""
        Request = self.env['stock.adjustment.request'].sudo()
        created = Request
        for quant in self:
            current = sum(self.sudo()._gather(
                quant.product_id, quant.location_id,
                lot_id=quant.lot_id or None, package_id=quant.package_id or None,
                owner_id=quant.owner_id or None, strict=True).mapped('quantity'))
            counted = quant.inventory_quantity
            created |= Request.create({
                'product_id': quant.product_id.id,
                'location_id': quant.location_id.id,
                'lot_id': quant.lot_id.id or False,
                'package_id': quant.package_id.id or False,
                'owner_id': quant.owner_id.id or False,
                'current_qty': current,
                'counted_qty': counted,
                'diff_qty': counted - current,
                'reason': reason,
                'requested_by': self.env.user.id,
                'company_id': (quant.company_id or self.env.company).id,
            })
        return created

    def _nns_create_adjustment_requests(self, reason):
        """Wizard (Inventory Adjustment 'Apply') path: build requests, then
        discard the unapplied counted values so the quant returns to display
        without changing stock."""
        created = self._nns_build_requests(reason)
        quants_to_reset = self.filtered(lambda q: q.inventory_quantity_set)
        quants_to_reset.write({'inventory_quantity_set': False})
        return created

    # ------------------------------------------------------------------
    # Core chokepoint override
    # ------------------------------------------------------------------
    def _update_available_quantity(self, product_id, location_id, quantity=False,
                                   reserved_quantity=False, lot_id=None,
                                   package_id=None, owner_id=None, in_date=None):
        # Only consider real on-hand decrements (ignore reservation-only updates).
        if quantity:
            decision = self._nns_evaluate(product_id, location_id, quantity,
                                          lot_id=lot_id, package_id=package_id,
                                          owner_id=owner_id)
            if decision:
                self._nns_enforce(decision)
        return super()._update_available_quantity(
            product_id, location_id, quantity=quantity,
            reserved_quantity=reserved_quantity, lot_id=lot_id,
            package_id=package_id, owner_id=owner_id, in_date=in_date)

    # ------------------------------------------------------------------
    # Decision logic
    # ------------------------------------------------------------------
    def _nns_evaluate(self, product_id, location_id, quantity, lot_id=None,
                      package_id=None, owner_id=None):
        """Return a dict describing a negative-stock event to enforce, or None.

        Returns None when the operation is allowed (feature off, not storable,
        virtual location, increment, exception set, or result not negative).
        """
        uom = product_id.uom_id

        # Only decrements of storable products at internal locations matter.
        if uom.compare(quantity, 0) >= 0:
            return None
        if not product_id.is_storable:
            return None
        if location_id.usage != 'internal':
            return None

        company = location_id.company_id or self.env.company
        if not company.nns_enabled:
            return None

        # 3-tier exception: product / category (with parents) / location.
        if product_id.product_tmpl_id.nns_allow_negative:
            return None
        if location_id.nns_allow_negative:
            return None
        category = product_id.categ_id
        if category and category._nns_allows_negative():
            return None

        # Compute the resulting on-hand at this exact characteristic set.
        # This is the authoritative figure that drives the BLOCK decision.
        current = self.sudo()._get_available_quantity(
            product_id, location_id, lot_id=lot_id, package_id=package_id,
            owner_id=owner_id, strict=True, allow_negative=True)
        resulting = current + quantity
        if uom.compare(resulting, 0) >= 0:
            return None

        # For the user-facing log/message, prefer document-level numbers captured
        # before Odoo's sub-step decrements (see stock.move.line._action_done).
        # Odoo splits one move into several quant writes, so the quant-level
        # `current`/`quantity` can look smaller than what the user entered.
        snapshot = self.env.context.get('nns_snapshot') or {}
        snap = snapshot.get((product_id.id, location_id.id))
        if snap:
            report_current = snap['on_hand']
            report_requested = snap['requested']
            report_resulting = report_current - report_requested
        else:
            report_current = current
            report_requested = abs(quantity)
            report_resulting = resulting

        return {
            'company': company,
            'product': product_id,
            'location': location_id,
            'current': report_current,
            'requested': report_requested,
            'resulting': report_resulting,
            'shortfall': abs(report_resulting),
        }

    # ------------------------------------------------------------------
    # Enforcement (block / warn / override)
    # ------------------------------------------------------------------
    def _nns_enforce(self, decision):
        company = decision['company']
        mode = company.nns_mode
        override_ok = bool(self.env.context.get('nns_override_ok'))

        if override_ok:
            # A manager approved this through the override wizard. The operation
            # proceeds, so the log lives in the same (successful) transaction.
            log = self._nns_create_log(decision, 'override',
                                       reason=self.env.context.get('nns_override_reason'))
            log._notify_alert_users()
            return  # allow the operation to proceed

        # Both modes stop the operation here by raising. A raise rolls back the
        # current transaction, so the log MUST be written on an independent
        # cursor or it would vanish with the rollback.
        self._nns_log_independent(decision, 'warn' if mode == 'warn' else 'block')
        raise UserError(self._nns_error_message(decision, mode))

    def _nns_log_vals(self, decision, event_type, reason=None):
        location = decision['location']
        return {
            'event_type': event_type,
            'product_id': decision['product'].id,
            'location_id': location.id,
            'warehouse_id': location.warehouse_id.id or False,
            'current_qty': decision['current'],
            'move_qty': decision['requested'],
            'resulting_qty': decision['resulting'],
            'shortfall_qty': decision['shortfall'],
            'reference': self.env.context.get('nns_document_ref') or False,
            'reason': reason or False,
            'user_id': self.env.user.id,
            'company_id': decision['company'].id,
        }

    def _nns_create_log(self, decision, event_type, reason=None):
        return self.env['stock.sentinel.log'].sudo().create(
            self._nns_log_vals(decision, event_type, reason=reason))

    def _nns_log_independent(self, decision, event_type, reason=None):
        """Persist a block/warn log on a fresh cursor so it survives the
        UserError rollback that immediately follows. Alert activities are
        scheduled on the same independent transaction."""
        vals = self._nns_log_vals(decision, event_type, reason=reason)
        try:
            with self.pool.cursor() as new_cr:
                new_env = self.env(cr=new_cr)
                log = new_env['stock.sentinel.log'].sudo().create(vals)
                log._notify_alert_users()
                # Commit explicitly so the log survives the UserError rollback.
                new_cr.commit()
        except Exception:  # pragma: no cover - logging must never mask the block
            # Never let a logging failure swallow the negative-stock block.
            pass

    def _nns_fmt(self, qty, product):
        """Format a quantity using the product's UoM rounding, trimming
        trailing zeros so values read as 3 instead of 3.0000."""
        precision = (product.uom_id and product.uom_id.rounding) or 0.01
        digits = max(0, len(str(precision).split('.')[-1])) if '.' in str(precision) else 0
        text = f"{qty:.{digits}f}" if digits else f"{qty:.0f}"
        if '.' in text:
            text = text.rstrip('0').rstrip('.')
        return text

    def _nns_error_message(self, decision, mode):
        product = decision['product']
        uom = product.uom_id.name or _('Units')
        fmt = lambda q: self._nns_fmt(q, product)

        # Plain-text layout: a clear headline, an aligned label/value block and
        # a divider. UserError renders as plain text (Odoo escapes HTML), so we
        # use spacing and a rule line for readability rather than markup.
        lines = [
            _("Negative stock would result from this operation."),
            "",
            _("  Product    %s") % product.display_name,
            _("  Location   %s") % decision['location'].display_name,
            "  " + ("-" * 44),
            _("  On hand    %(qty)s %(uom)s") % {'qty': fmt(decision['current']), 'uom': uom},
            _("  Requested  %(qty)s %(uom)s") % {'qty': fmt(decision['requested']), 'uom': uom},
            _("  Resulting  %(qty)s %(uom)s") % {'qty': fmt(decision['resulting']), 'uom': uom},
            _("  Shortfall  %(qty)s %(uom)s") % {'qty': fmt(decision['shortfall']), 'uom': uom},
        ]
        msg = "\n".join(lines)

        if mode == 'warn':
            msg += _(
                "\n\nThis operation is blocked. An Inventory Manager can force it "
                "through using the 'Override Negative Stock' button on the document, "
                "providing a reason."
            )
        else:
            msg += _(
                "\n\nReceive or adjust stock for this product, or set an "
                "'Allow Negative Stock' exception, then try again."
            )
        return msg
