# -*- coding: utf-8 -*-

import math
from odoo import api, models


class ProductAutoBarcode(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, vals):
        """generate barcode when create new product"""
        res = super(ProductAutoBarcode, self).create(vals)
        ean = generate_ean(str(res.id))
        res.barcode = '21' + ean
        return res


def ean_checksum(eancode):
    """returns the checksum of an ean string of length 13, returns -1 if
    the string has the wrong length"""
    if len(eancode) != 13:
        return -1
    oddsum = 0
    evensum = 0
    eanvalue = eancode
    reversevalue = eanvalue[::-1]
    finalean = reversevalue[1:]

    for i in range(len(finalean)):
        if i % 2 == 0:
            oddsum += int(finalean[i])
        else:
            evensum += int(finalean[i])
    total = (oddsum * 3) + evensum

    check = int(10 - math.ceil(total % 10.0)) % 10
    return check


def check_ean(eancode):
    """returns True if eancode is a valid ean13 string, or null"""
    if not eancode:
        return True
    if len(eancode) != 13:
        return False
    try:
        int(eancode)
    except:
        return False
    return ean_checksum(eancode)


def generate_ean(ean):
    """Creates and returns a valid ean13 from an invalid one"""
    if not ean:
        return "0000000000000"
    product_identifier = '00000000000' + ean
    ean = product_identifier[-11:]
    check_number = check_ean(ean + '00')
    return f'{ean}0{check_number}'


class ProductTemplateAutoBarcode(models.Model):
    _inherit = 'product.template'

    
    @api.model
    def create(self, vals_list):
        """generate barcode number when create new product"""
        templates = super(ProductTemplateAutoBarcode, self).create(vals_list)
        ean = generate_ean(str(templates.id))
        templates.barcode = '22' + ean
        return templates
    
    def generate_barcode(self):
        for rec in self:
            ean = generate_ean(str(rec.id))
            rec.barcode = '22' + ean
