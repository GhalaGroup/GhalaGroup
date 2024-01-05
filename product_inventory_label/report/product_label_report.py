from odoo import api, models,fields,_
from collections import defaultdict
from odoo.exceptions import UserError
from PIL import Image
import requests
import sys
import json
import urllib.request
import math
import io

class ReportInventoryLabel(models.AbstractModel):
    _name = "report.product_inventory_label.label_product_inventory_view"
    
    
    def _get_report_values(self,docids,data):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if data.get('active_model') == 'product.template':
            Product = self.env['product.template']
        elif data.get('active_model') == 'product.product':
            Product = self.env['product.product']
        else:
            raise UserError(_('Product model not defined, Please contact your administrator.'))
        quantity_by_product = defaultdict(list)
        for p,q in data.get('quantity_by_product').items():
            product = Product.browse(int(p))
            quantity_by_product[product].append((product.barcode,q))
            lot_number = self.env['stock.lot'].search([('product_id','=',int(p))])
            data['lot_number'] = lot_number.name
            data['id'] = p
            product_id = product.id if data.get('active_model') == 'product.template' else product.product_tmpl_id.id
            product_image_url = base_url+"/web/image?model=%s&id=%s&field=%s" % (data.get('active_model'),int(p),'image_1920')
        if data.get('custom_barcodes'):
            for product,barcode_qtys in data.get('custom_barcodes').items():
                quantity_by_product[Product.browse(int(product))] += barcode_qtys
        data['quantity'] = quantity_by_product
        # self.show_label_data(data)
        logo_url = base_url+"/web/image?model=res.company&id=%s&field=%s" %(self.env.user.company_id.id,'logo')
        
        logo = self.decode_image_from_url(logo_url)
        product_image = self.decode_image_from_url(product_image_url,size=(150,150))
        data.update({'logo':logo,'image':product_image})
        print("ZPL DATA",data)
        return data
    

    def decode_image_from_url(self,image_url,size=(None,None)):
        headers = {'Accept':'application/json'}
        urllib.request.urlretrieve(image_url,'zpl_image.png')
        img = Image.open('zpl_image.png', mode='r')
        current_width, current_height = img.size
        new_width, new_height = size
        width = new_width if new_width else math.ceil(current_width/2)
        height = new_height if new_height else math.ceil(current_height/2)
        new_size = (width,height)
        resized_img = img.resize(new_size)
        img_byte_array = io.BytesIO()
        resized_img.save(img_byte_array,format='PNG')
        formData = {'file':img_byte_array.getvalue()}
        zpl_url = "https://api.labelary.com/v1/graphics"
        response = requests.post(url=zpl_url, files=formData, headers=headers)
        zpl_data = json.loads(response.text)
        return zpl_data

    
    def show_label_data(self,data):
        # print("Data2", data)
        product = ""
        for item in data['quantity'].items():
            print("Item", item)
            product = item[0]
        # print("product","name:%s,category:%s,cbm:%s,quantity:%f,image:%s,is_variant:%s" % (product.name,product.categ_id.name,product.volume,product.qty_available,type(product.image_1920),product.is_product_variant))
        # print("Company Info",self.env.user.company_id.website)
        # print("Image",type(product.image_128),product.image_128)
        for variant in product.product_template_variant_value_ids:
            value = variant.display_name.split(':')
            print("%s (%s)" %(value[1],value[0]),end=',')
        lot = self.env['stock.lot'].search([('product_id','=',product.id)])
        # print("company logo: ",self.env.user.company_id.logo)
        # print("Decode company logo",self.env.user.company_id.logo.decode(encoding='utf-8', errors='strict'))
        print("Logo isascii:%s" %(self.env.user.company_id.logo))
        print("logo lines",len(self.env.user.company_id.logo))
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        image_url = base_url+"/web/image?model=res.company&id=%s&field=%s" %(self.env.user.company_id.id,'logo')
        img = Image.open(requests.get(image_url, stream=True).raw)
        print("Img",img.size,image_url)
        print("Image Width",img.width)
        print("Image Size",sys.getsizeof(self.env.user.company_id.logo))
        
        
         