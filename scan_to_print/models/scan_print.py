from odoo import api, fields, models, _, tools
import logging


_logger = logging.getLogger(__name__)
class ScanToPrint(models.Model):
    _name = 'scan.to.print'
    _logger.debug("This is my debug message ! ")
