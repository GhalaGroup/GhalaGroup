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

import logging
import pprint

import requests
import werkzeug
from werkzeug.utils import redirect
import json

from odoo import http
from odoo.http import request
_logger = logging.getLogger(__name__)


class AtomController(http.Controller):
    @http.route(['/payment/ngenius/return/', '/payment/ngenius/cancel/', '/payment/ngenius/error/'],
                type='http', auth='public', csrf=False)
    def ngenius_return(self, **post):
        """ ngenius."""

        _logger.info(
            'ngenius: entering form_feedback with post data %s', pprint.pformat(post))
        if post:
            url = 'https://api-gateway.stanbicbank.co.tz/identity/auth/access-token?realName=sandboxStanbicBankTZA'
            headers = {
                'Authorization': 'Basic MWYzMjY3N2YtMmQ0Ny00YTY2LWI1YmMtYWExYTY1MDUzZWY2OmE5OTYxNWZiLTA5NWItNDQwZC1iNWI5LTU0YWRmNDZhNzc1YQ==',
                'Content-Type': 'application/vnd.ni-identity.v1+json'}

            r = requests.post(url, headers=headers)
            json_data = json.loads(r.text)
            _token = json_data['access_token']
            outlet = "910b7993-c0e2-48fa-b246-b9fd7332b6de"
            url = "https://api-gateway.stanbicbank.co.tz/transactions/outlets/" + outlet + "/orders/" + post["ref"]
            headers = {
                'Authorization': 'Bearer ' + _token,
                'Accept': 'application/vnd.ni-payment.v2+json',
            }

            r = requests.get(url, headers=headers)
            json_data = json.loads(r.text)
            request.env['payment.transaction'].sudo().form_feedback(json_data, 'ngenius')
        return werkzeug.utils.redirect('/payment/process')

    @http.route(['/payment/ngenius/forward/'],
                type='http', auth='public', csrf=False)
    def ngenius_forward(self, **post):
        """ forward te request as get insted of post"""
        if post:
            return redirect(post['url'])
        return redirect("https://madfox.solutions")
