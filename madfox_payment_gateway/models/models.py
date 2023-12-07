# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import api, fields, models
from datetime import datetime
from werkzeug import urls
from odoo.tools import consteq, float_round, image_process, ustr
import requests
import hashlib
import json

import base64

import logging

_logger = logging.getLogger(__name__)


class PaymentAcquirerAtom(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[
        ('ngenius', 'Ngenius')
    ], ondelete={'ngenius': 'cascade'})
    #fields.Selection(selection_add=[('ngenius', 'Ngenius')], ondelete={'paypal': 'set default'})
    ngenius_merchant_id = fields.Char('Merchant ID', required_if_provider='ngenius',
                                        groups='base.group_user')
    ngenius_merchant_key = fields.Char('Merchent Key', required_if_provider='ngenius',
                                        groups='base.group_user')


    @api.model
    def _get_ngenius_urls(self):
        """ Atom URLS """
        url = 'https://api-gateway.stanbicbank.co.tz/identity/auth/access-token?realName=sandboxStanbicBankTZA'
        headers = {
            'Authorization': 'Basic MWYzMjY3N2YtMmQ0Ny00YTY2LWI1YmMtYWExYTY1MDUzZWY2OmE5OTYxNWZiLTA5NWItNDQwZC1iNWI5LTU0YWRmNDZhNzc1YQ==',
            'Content-Type': 'application/vnd.ni-identity.v1+json'}

        r = requests.post(url, headers=headers)
        json_data = json.loads(r.text)
        _token = json_data['access_token']
        outlet = "910b7993-c0e2-48fa-b246-b9fd7332b6de"
        url = "https://api-gateway.stanbicbank.co.tz/transactions/outlets/"+outlet+"/orders"
        headers = {
            'Authorization': 'Bearer '+_token,
            'Content-Type': 'application/vnd.ni-payment.v2+json',
            'Accept':'application/vnd.ni-payment.v2+json',
        }
        payload = {
            'action': 'SALE',
            'amount': {
                'currencyCode': 'TZS',
                'value': '1000000'

            }
        }
        r = requests.post(url, headers=headers, data=json.dumps(payload))
        json_data = json.loads(r.text)
        return {
            #'ngenius_form_url':'https://securegw-stage.ngenius.in/order/process'
            'ngenius_form_url':json_data['_links']['payment']['href']
        }

    @api.model
    def get_ngenius_urls(self, values):
        """ Atom URLS """
        url = 'https://api-gateway.stanbicbank.co.tz/identity/auth/access-token?realName=sandboxStanbicBankTZA'
        headers = {
            'Authorization': 'Basic MWYzMjY3N2YtMmQ0Ny00YTY2LWI1YmMtYWExYTY1MDUzZWY2OmE5OTYxNWZiLTA5NWItNDQwZC1iNWI5LTU0YWRmNDZhNzc1YQ==',
            'Content-Type': 'application/vnd.ni-identity.v1+json'}

        r = requests.post(url, headers=headers)
        json_data = json.loads(r.text)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        _token = json_data['access_token']
        outlet = "910b7993-c0e2-48fa-b246-b9fd7332b6de"
        url = "https://api-gateway.stanbicbank.co.tz/transactions/outlets/"+outlet+"/orders"
        headers = {
            'Authorization': 'Bearer '+_token,
            'Content-Type': 'application/vnd.ni-payment.v2+json',
            'Accept':'application/vnd.ni-payment.v2+json',
        }

        payload = {
            'action': 'SALE',
            'amount': {
                'currencyCode': 'TZS',
                'value': int(values['amount']*100)

            },
            'merchantAttributes': {
                'redirectUrl': urls.url_join(base_url, '/payment/ngenius/return'),
                'cancelUrl': urls.url_join(base_url, '/payment/ngenius/cancel'),
            },
            'merchantOrderReference': values['reference'],

        }
        r = requests.post(url, headers=headers, data=json.dumps(payload))
        json_data = json.loads(r.text)
        _logger.info(json_data)
        return '/payment/ngenius/forward/?url='+json_data['_links']['payment']['href']


    def ngenius_get_form_action_url(self):
        return self._get_ngenius_urls () ['ngenius_form_url']

    def ngenius_form_generate_values(self ,values):
        self.ensure_one ()
        base_url=self.env ['ir.config_parameter'].sudo ().get_param ('web.base.url')
        now=datetime.now ()

        ngenius_values=dict (
                          MID=self.ngenius_merchant_id ,
                          ORDER_ID=str(values ['reference']) ,
                          CUST_ID = str(values.get('partner_id')),
                          INDUSTRY_TYPE_ID='Retail' ,
                          CHANNEL_ID = 'WEB',
                          TXN_AMOUNT=str(values ['amount']) ,
                          WEBSITE='WEBSTAGING',
                          EMAIL=str(values.get ('partner_email')) ,
                          MOBILE_NO = str(values.get('partner_phone')),
                          CALL_BACK_URL=urls.url_join (base_url, '/payment/ngenius/return/'),
                          tx_url='facebook.com',
                          )

        return ngenius_values


    def render(self, reference, amount, currency_id, partner_id=False, values=None):
        """ Renders the form template of the given acquirer as a qWeb template.
        :param string reference: the transaction reference
        :param float amount: the amount the buyer has to pay
        :param currency_id: currency id
        :param dict partner_id: optional partner_id to fill values
        :param dict values: a dictionary of values for the transction that is
        given to the acquirer-specific method generating the form values

        All templates will receive:

         - acquirer: the payment.acquirer browse record
         - user: the current user browse record
         - currency_id: id of the transaction currency
         - amount: amount of the transaction
         - reference: reference of the transaction
         - partner_*: partner-related values
         - partner: optional partner browse record
         - 'feedback_url': feedback URL, controler that manage answer of the acquirer (without base url) -> FIXME
         - 'return_url': URL for coming back after payment validation (wihout base url) -> FIXME
         - 'cancel_url': URL if the client cancels the payment -> FIXME
         - 'error_url': URL if there is an issue with the payment -> FIXME
         - context: Odoo context

        """
        if values is None:
            values = {}

        if not self.view_template_id:
            return None

        values.setdefault('return_url', '/payment/ngenius/return/')
        # reference and amount
        values.setdefault('reference', reference)
        amount = float_round(amount, 2)
        values.setdefault('amount', amount)

        # currency id
        currency_id = values.setdefault('currency_id', currency_id)
        if currency_id:
            currency = self.env['res.currency'].browse(currency_id)
        else:
            currency = self.env.company.currency_id
        values['currency'] = currency

        # Fill partner_* using values['partner_id'] or partner_id argument
        partner_id = values.get('partner_id', partner_id)
        billing_partner_id = values.get('billing_partner_id', partner_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            if partner_id != billing_partner_id:
                billing_partner = self.env['res.partner'].browse(billing_partner_id)
            else:
                billing_partner = partner
            values.update({
                'partner': partner,
                'partner_id': partner_id,
                'partner_name': partner.name,
                'partner_lang': partner.lang,
                'partner_email': partner.email,
                'partner_zip': partner.zip,
                'partner_city': partner.city,

                'partner_country': partner.country_id,
                'partner_phone': partner.phone,
                'partner_state': partner.state_id,
                'billing_partner': billing_partner,
                'billing_partner_id': billing_partner_id,
                'billing_partner_name': billing_partner.name,
                'billing_partner_commercial_company_name': billing_partner.commercial_company_name,
                'billing_partner_lang': billing_partner.lang,
                'billing_partner_email': billing_partner.email,
                'billing_partner_zip': billing_partner.zip,
                'billing_partner_city': billing_partner.city,

                'billing_partner_country_id': billing_partner.country_id.id,
                'billing_partner_country': billing_partner.country_id,
                'billing_partner_phone': billing_partner.phone,
                'billing_partner_state': billing_partner.state_id,
            })
        my_url=''
        if self.provider == 'ngenius':
            my_url = self.get_ngenius_urls(values)
        else:
            my_url= self._context.get('tx_url', self.get_form_action_url())

        values.update({
            'tx_url': my_url,
            'submit_class': self._context.get('submit_class', 'btn btn-link'),
            'submit_txt': self._context.get('submit_txt'),
            'acquirer': self,
            'user': self.env.user,
            'context': self._context,
            'type': 'get',
           # 'type': values.get('type') or 'form',
        })

        return self.view_template_id._render(values, engine='ir.qweb')


class PaymentTransactionAtom(models.Model):
    _inherit = 'payment.transaction'

    ngenius_txn_type = fields.Char('Transaction type')

    @api.model
    def _ngenius_form_get_tx_from_data(self, data):
        reference = data.get('merchantOrderReference')
        if not reference:
            error_msg=_ ('Paytm: received data with missing reference (%s)') % (reference)
            _logger.info(error_msg)
            raise ValidationError (error_msg)

        reference = data['merchantOrderReference']

        txs=self.env ['payment.transaction'].search ([('reference' ,'=' ,reference)])
        if not txs or len (txs) > 1:
            error_msg='ngenius: received data for reference %s' % (reference)
            if not txs:
                error_msg+='; no order found'
            else:
                error_msg+='; multiple order found'
            _logger.info (error_msg)
            raise ValidationError (error_msg)
        return txs [0]


    def _ngenius_form_get_invalid_parameters(self ,data):
        invalid_parameters=[]
        if self.acquirer_reference and data.get ('mmp_txn') != self.acquirer_reference and False:
            invalid_parameters.append(('ORDERID', data.get('merchantOrderReference'), self.acquirer_reference))

        return invalid_parameters

    def _ngenius_form_validate(self ,data):
        status=data['_embedded']['payment'][0]['state']
        result=self.write ({
            'acquirer_reference':self.env ['payment.acquirer'].search ([]) ,
            'date':fields.Datetime.now () ,

        })
        if status == 'CAPTURED':
            self._set_transaction_done ()
        elif status != 'CANCELLED':
            self._set_transaction_cancel ()
        else:
            self._set_transaction_pending ()
        return result
