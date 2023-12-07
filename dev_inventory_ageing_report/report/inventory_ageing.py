# -*- coding: utf-8 -*-


from odoo import api, models
from dateutil.relativedelta import relativedelta


class inventory_ageing_report(models.AbstractModel):
    _name = 'report.dev_inventory_ageing_report.inventory_ageing_template_id'
    _description = 'Inventory Ageing Report '

#    def get_top_product_data(self, record):
#        return "Gopal"

    def get_aging_detail(self,record):
        res = {}
        period_length = record.period_length
        start = record.date_from
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

    def create_table_header(self,record,res):
        record_list = {'col_0':'Code',
                        'col_1':'Product','col_2':'Total Qty','col_3':'Total Value',
                       'col_4':'Qunatity','col_5':'Value',
                       'col_4_header':res['6']['name'],
                       'col_6':'Qunatity','col_7':'Value',
                       'col_6_header':res['5']['name'],
                        'col_8':'Qunatity','col_9':'Value',
                        'col_8_header':res['4']['name'],
                        'col_10':'Qunatity','col_11':'Value',
                        'col_10_header':res['3']['name'],
                        'col_12':'Qunatity','col_13':'Value',
                        'col_12_header':res['2']['name'],
                        'col_14':'Qunatity','col_15':'Value',
                        'col_14_header':res['1']['name'],
                        'col_16':'Qunatity','col_17':'Value',
                        'col_16_header':res['0']['name'], 
                    }
        
        return record_list

    def get_products(self,record):
        product_pool=record.env['product.product']
        if not record.filter_by:
            return product_pool.search([('type','=','product')])
        else:
            if record.filter_by == 'by_product':
                if record.product_ids:
                    return record.product_ids
            else:
                product_ids = product_pool.search([('categ_id','child_of',record.category_id.id),('type','=','product')])
                if product_ids:
                    return product_ids
                else:
                    raise ValidationError("Product not found in selected category !!!")

    def get_aging_quantity(self,record,product,to_date=False):
        if to_date:
            product = product.with_context(to_date=to_date)
        if record.warehouse_ids:
            product = product.with_context(warehouse=record.warehouse_ids.ids)
        if record.location_ids:
            product = product.with_context(location=record.location_ids.ids)

        return product.qty_available

    def create_table_values(self,record,res,product_ids):
        lst=[0,0,0,0,0,0,0]
        lst_val=[0,0,0,0,0,0,0]
#        row = row+1
        total_qty = total_val=0
        table_values = []
        for product in product_ids:
            stock_qty = self.get_aging_quantity(record,product,record.date_from)
            total_qty += stock_qty
            total_val += stock_qty * product.standard_price
            quantity_values = {}
            table_values.append({'col_0':product.default_code,'col_1':product.name,
                                'col_2':stock_qty,'col_3':stock_qty * product.standard_price,
                                'quantity_values':quantity_values
                                })
            col_qty = 5
            for i in range(7)[::-1]:
                from_qty = to_qty = 0
                from_qty = self.get_aging_quantity(record,product,res[str(i)]['stop'])
                if res[str(i)]['start']:
                    to_qty = self.get_aging_quantity(record,product,res[str(i)]['start'])
                qty = from_qty - to_qty
                lst[i] += qty
                lst_val[i] += qty * product.standard_price
                quantity_values['col_'+str(col_qty)] = qty
                quantity_values['col_'+str(col_qty+1)] = qty * product.standard_price or 0
                col_qty += 2
        
#        
        
        return table_values


#    res = self.get_aging_detail()
    def _get_report_values(self, docids, data=None):
        docs = self.env['inventory.age.wizard'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'inventory.age.wizard',
            'docs': docs,
            'get_aging_detail': self.get_aging_detail,
            'get_products':self.get_products,
            'create_table_header':self.create_table_header,
            'create_table_values':self.create_table_values
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
