# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.web.controllers.report import ReportController
from odoo.tools.safe_eval import safe_eval
from odoo.http import content_disposition
from werkzeug.urls import url_parse
import time
import logging
import json

_logger = logging.getLogger(__name__)


class VPAReportController(ReportController):
    """Override to add debugging for print_report_name evaluation"""

    @http.route()
    def report_download(self, data, context=None, token=None, readonly=True):
        """Override to debug print_report_name evaluation"""
        requestcontent = json.loads(data)
        url, type_ = requestcontent[0], requestcontent[1]

        reportname = '???'

        try:
            if type_ in ['qweb-pdf', 'qweb-text']:
                converter = 'pdf' if type_ == 'qweb-pdf' else 'text'
                extension = 'pdf' if type_ == 'qweb-pdf' else 'txt'

                pattern = '/report/pdf/' if type_ == 'qweb-pdf' else '/report/text/'
                reportname = url.split(pattern)[1].split('?')[0]

                docids = None
                if '/' in reportname:
                    reportname, docids = reportname.split('/')

                _logger.info(f"📄 VPA Report Download - reportname: {reportname}, docids: {docids}, type: {type_}")

                if docids:
                    # Generic report:
                    response = self.report_routes(reportname, docids=docids, converter=converter, context=context)
                else:
                    # Particular report:
                    data_dict = url_parse(url).decode_query(cls=dict)
                    if 'context' in data_dict:
                        context_parsed, data_context = json.loads(context or '{}'), json.loads(data_dict.pop('context'))
                        context = json.dumps({**context_parsed, **data_context})
                    response = self.report_routes(reportname, converter=converter, context=context, **data_dict)

                # Search directly for the report instead of using _get_report_from_name
                _logger.info(f"📄 Searching for reportname: {reportname}")

                report_search = http.request.env['ir.actions.report'].sudo().search([
                    ('report_name', '=', reportname)
                ], limit=1)

                _logger.info(f"📄 Direct search found: ID={report_search.id if report_search else 'None'}")

                if not report_search:
                    # Fallback to _get_report_from_name
                    _logger.info(f"📄 No direct search result, trying _get_report_from_name")
                    report = http.request.env['ir.actions.report']._get_report_from_name(reportname)
                    _logger.info(f"📄 _get_report_from_name returned: ID={report.id}")
                else:
                    report = report_search

                filename = "%s.%s" % (report.name, extension)

                _logger.info(f"📄 Using Report ID: {report.id}, name={report.name}")
                _logger.info(f"📄 Report.print_report_name value: '{report.print_report_name}'")

                if docids:
                    ids = [int(x) for x in docids.split(",") if x.isdigit()]
                    obj = http.request.env[report.model].browse(ids)

                    _logger.info(f"📄 Object count: {len(obj)}, IDs: {ids}")

                    # For VPA templates, get the print expression from the template directly
                    if 'vpa_document_layout.report_template_' in reportname and len(obj) == 1:
                        try:
                            # Extract template ID
                            template_id = int(reportname.split('_')[-1])
                            _logger.info(f"📄 VPA template detected, ID: {template_id}")

                            # Get template and its print_name_pattern
                            template = http.request.env['vpa.document.template'].sudo().browse(template_id)
                            if template.exists():
                                # Use template's method to get expression
                                expression = template._get_print_name_expression()
                                _logger.info(f"📄 Got expression from template: {expression}")

                                if expression:
                                    # safe_eval doesn't allow the time module, so we pass an empty dict for time
                                    # Our expressions don't actually use time, only object
                                    report_name = safe_eval(expression, {'object': obj})
                                    filename = "%s.%s" % (report_name, extension)
                                    _logger.info(f"✅ VPA custom filename: {filename}")
                        except Exception as e:
                            _logger.error(f"❌ VPA filename generation failed: {e}", exc_info=True)

                    # Standard Odoo report evaluation
                    elif report.print_report_name and not len(obj) > 1:
                        _logger.info(f"📄 Evaluating standard report expression: {report.print_report_name}")
                        try:
                            # Don't pass time module - safe_eval doesn't allow it
                            # Standard Odoo expressions typically don't use time anyway
                            report_name = safe_eval(report.print_report_name, {'object': obj})
                            filename = "%s.%s" % (report_name, extension)
                            _logger.info(f"✅ Standard report filename: {filename}")
                        except Exception as eval_err:
                            _logger.error(f"❌ Expression evaluation failed: {eval_err}", exc_info=True)

                response.headers.add('Content-Disposition', content_disposition(filename))
                _logger.info(f"📄 Final filename set: {filename}")
                return response
            else:
                return super().report_download(data, context=context, token=token, readonly=readonly)
        except Exception as e:
            _logger.warning("Error while generating report %s", reportname, exc_info=True)
            return super().report_download(data, context=context, token=token, readonly=readonly)
