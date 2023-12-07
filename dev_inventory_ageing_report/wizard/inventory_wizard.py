# -*- coding: utf-8 -*-


from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
#========For Excel========
from io import BytesIO
import xlwt
from xlwt import easyxf
import base64
# =====================

class inventory_wizard(models.TransientModel):
    _name = 'inventory.age.wizard'
    _description = 'Inventory Ageing'
    
    
    date_from = fields.Date('Date', required="1")
    company_id = fields.Many2one('res.company', string='Company', required="1", default=lambda self:self.env.user.company_id.id)
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouse', required="1")
    location_ids = fields.Many2one('stock.location', string='Locations')
    period_length = fields.Integer('Period Length (Days)', default=30, required="1")
    filter_by = fields.Selection([('by_product','Product'),('by_category','Product Category')], string='Filter By')
    product_ids = fields.Many2many('product.product', string='Product', domain=[('type','=','product')])
    category_id = fields.Many2one('product.category', string='Product Category')
    excel_file = fields.Binary('Excel File')


    def print_pdf(self):
        data = {}
        data['form'] = self.read()[0]
        return self.env.ref('dev_inventory_ageing_report.'
                            'inventory_age_pdf_report').report_action(
            self, data=None)

    
    def get_products(self):
        product_pool=self.env['product.product']
        if not self.filter_by:
            return product_pool.search([('type','=','product')])
        else:
            if self.filter_by == 'by_product':
                if self.product_ids:
                    return self.product_ids
            else:
                product_ids = product_pool.search([('categ_id','child_of',self.category_id.id),('type','=','product')])
                if product_ids:
                    return product_ids
                else:
                    raise ValidationError("Product not found in selected category !!!")
                   
                    
    def get_style(self):
        main_header_style = easyxf('font:height 300;'
                                   'align: horiz center;font: color black; font:bold True;'
                                   "borders: top thin,left thin,right thin,bottom thin")
                                   
        header_style = easyxf('font:height 200;pattern: pattern solid, fore_color gray25;'
                              'align: horiz center;font: color black; font:bold True;'
                              "borders: top thin,left thin,right thin,bottom thin")
        
        left_header_style = easyxf('font:height 200;pattern: pattern solid, fore_color gray25;'
                              'align: horiz left;font: color black; font:bold True;'
                              "borders: top thin,left thin,right thin,bottom thin")
        
        
        text_left = easyxf('font:height 200; align: horiz left;')
        
        text_right = easyxf('font:height 200; align: horiz right;', num_format_str='0.00')
        
        text_left_bold = easyxf('font:height 200; align: horiz right;font:bold True;')
        
        text_right_bold = easyxf('font:height 200; align: horiz right;font:bold True;', num_format_str='0.00') 
        text_center = easyxf('font:height 200; align: horiz center;'
                             "borders: top thin,left thin,right thin,bottom thin")  
        
        return [main_header_style, left_header_style,header_style, text_left, text_right, text_left_bold, text_right_bold, text_center]
        
        
    
    
    def create_excel_header(self,worksheet,main_header_style,left_header_style,text_left):
        worksheet.write_merge(0, 1, 2, 5, 'Stock Inventory Aging', main_header_style)
        row = 3
        col=1
        worksheet.write(row,col, 'Date', left_header_style)
        date = datetime.strftime(self.date_from, "%d-%m-%Y")
        worksheet.write_merge(row,row, col+1, col+2, date, text_left)
        worksheet.write(row,col+3, 'Period Length', left_header_style)
        worksheet.write_merge(row,row, col+4, col+5, self.period_length, text_left)
        
        row+=1
        worksheet.write(row,col, 'Company', left_header_style)
        worksheet.write_merge(row,row, col+1, col+2, self.company_id.name or '', text_left)
        if self.filter_by:
            worksheet.write(row,col+3, 'Filter', left_header_style)
            if self.filter_by == 'by_product':
                worksheet.write_merge(row,row, col+4, col+5, 'Products', text_left)
            else:
                worksheet.write_merge(row,row, col+4, col+5, 'Product Category', text_left)
                
                
        row+=1
        worksheet.write(row,col, 'Warehouse', left_header_style)
        ware_name = ', '.join(map(lambda x: (x.name), self.warehouse_ids))
        worksheet.write_merge(row,row, col+1, col+2, ware_name or '', text_left)
        if self.filter_by and self.filter_by == 'by_category':
            worksheet.write(row,col+3, 'Product Category', left_header_style)
            worksheet.write_merge(row,row, col+4, col+5, self.category_id.name or '', text_left)
        
        if self.location_ids:
            row+=1
            worksheet.write(row,col, 'Location', left_header_style)
            location_name = ', '.join(map(lambda x: (x.name), self.location_ids))
            worksheet.write_merge(row,row, col+1, col+3, location_name or '', text_left)
            
        row+=1
        return worksheet, row
        
        
    def create_table_header(self,worksheet,header_style,row,res):
        worksheet.write_merge(row, row+1, 0, 0, 'Code', header_style)
        worksheet.write_merge(row,row+1, 1, 3, 'Product', header_style)
        worksheet.write_merge(row,row+1, 4, 4, 'Total Qty', header_style)
        worksheet.write_merge(row,row+1, 5, 5, 'Total Value', header_style)
        worksheet.write_merge(row,row, 6, 7, res['6']['name'], header_style)
        worksheet.write(row+1, 6, 'Qunatity', header_style)
        worksheet.write(row+1, 7, 'Value', header_style)
        worksheet.write_merge(row,row, 8, 9, res['5']['name'], header_style)
        worksheet.write(row+1, 8, 'Qunatity', header_style)
        worksheet.write(row+1, 9, 'Value', header_style)
        worksheet.write_merge(row,row, 10, 11, res['4']['name'], header_style)
        worksheet.write(row+1, 10, 'Qunatity', header_style)
        worksheet.write(row+1, 11, 'Value', header_style)
        worksheet.write_merge(row,row, 12, 13, res['3']['name'], header_style)
        worksheet.write(row+1, 12, 'Qunatity', header_style)
        worksheet.write(row+1, 13, 'Value', header_style)
        worksheet.write_merge(row,row, 14, 15, res['2']['name'], header_style)
        worksheet.write(row+1, 14, 'Qunatity', header_style)
        worksheet.write(row+1, 15, 'Value', header_style)
        worksheet.write_merge(row,row, 16, 17, res['1']['name'], header_style)
        worksheet.write(row+1, 16, 'Qunatity', header_style)
        worksheet.write(row+1, 17, 'Value', header_style)
        worksheet.write_merge(row,row, 18, 19, res['0']['name'], header_style)
        worksheet.write(row+1, 18, 'Qunatity', header_style)
        worksheet.write(row+1, 19, 'Value', header_style)
        row+=1
        return worksheet, row
    
    def get_aging_quantity(self,product,to_date=False):
        if to_date:
            product = product.with_context(to_date=to_date)
        if self.warehouse_ids:
            product = product.with_context(warehouse=self.warehouse_ids.ids)
        if self.location_ids:
            product = product.with_context(location=self.location_ids.ids)

        return product.qty_available
    
    def create_table_values(self,worksheet,text_left,text_right,row,res,product_ids,text_right_bold):
        lst=[0,0,0,0,0,0,0]
        lst_val=[0,0,0,0,0,0,0]
        row = row+1
        total_qty = total_val=0
        for product in product_ids:
            worksheet.write_merge(row,row, 0, 0, product.default_code, text_left)
            worksheet.write_merge(row,row, 1, 3, product.name, text_left)
            stock_qty = self.get_aging_quantity(product,self.date_from)
            total_qty += stock_qty
            total_val += stock_qty * product.standard_price
            worksheet.write(row, 4, stock_qty, text_right)
            worksheet.write(row, 5,stock_qty * product.standard_price, text_right)
            col=6
            for i in range(7)[::-1]:
                from_qty = to_qty = 0
                from_qty = self.get_aging_quantity(product,res[str(i)]['stop'])
                if res[str(i)]['start']:
                    to_qty = self.get_aging_quantity(product,res[str(i)]['start'])
                qty = from_qty - to_qty
                lst[i] += qty
                lst_val[i] += qty * product.standard_price
                worksheet.write(row,col, qty or 0, text_right)
                col+=1
                worksheet.write(row,col, qty * product.standard_price or 0, text_right)
                col+=1
            row+=1
#        
        worksheet.write_merge(row,row, 0, 2, 'TOTAL', text_right_bold)
        worksheet.write(row,4, total_qty or 0, text_right_bold)
        worksheet.write(row,5, total_val or 0, text_right_bold)
        col=6
        for i in range(7)[::-1]:
            worksheet.write(row,col, lst[i] or 0, text_right_bold)
            col+=1
            worksheet.write(row,col, lst_val[i] or 0, text_right_bold)
            col+=1
         
        return worksheet, row
        
        
    def get_aging_detail(self):
        res = {}
        period_length = self.period_length
        start = self.date_from
        for i in range(7)[::-1]:
            stop = start - relativedelta(days=period_length)
            res[str(i)] = {
                'name'  : (i != 0 and (str((7 - (i + 1)) * period_length) + '-' + str((7 - i) * period_length)) or ('+' + str(6 * period_length))),
                'value':'Values',
                'stop'  : start.strftime('%Y-%m-%d'),
                'start' : (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        return res
    
    def print_excel(self):
        product_ids = self.get_products()
        #====================================
        # Style of Excel Sheet 
        excel_style = self.get_style()
        main_header_style = excel_style[0]
        left_header_style = excel_style[1]
        header_style = excel_style[2]
        text_left = excel_style[3]
        text_right = excel_style[4]
        text_left_bold = excel_style[5]
        text_right_bold = excel_style[6]
        text_center = excel_style[7]
        # ====================================
        
        
        
        # Define Wookbook and add sheet 
        workbook = xlwt.Workbook()
        filename = 'Stock Inventory Aging.xls'
        worksheet = workbook.add_sheet('Stock Inventory Aging')
        for i in range(0,120):
            if i > 5:
                worksheet.col(i).width = 110 * 30
            else:
                worksheet.col(i).width = 130 * 30

        # Print Excel Header
        worksheet,row = self.create_excel_header(worksheet,main_header_style,left_header_style,text_left)
        res = self.get_aging_detail()
        worksheet, row = self.create_table_header(worksheet,header_style,row+2,res)
        worksheet, row = self.create_table_values(worksheet,text_left,text_right,row,res,product_ids,text_right_bold)
        
        
        
        
        
        #download Excel File
        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        excel_file = base64.encodestring(fp.read())
        fp.close()
        self.write({'excel_file': excel_file})

        if self.excel_file:
            active_id = self.ids[0]
            return {
                'type': 'ir.actions.act_url',
                'url': 'web/content/?model=inventory.age.wizard&download=true&field=excel_file&id=%s&filename=%s' % (
                    active_id, filename),
                'target': 'new',
            }
    
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
