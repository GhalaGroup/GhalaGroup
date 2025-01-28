# Copyright © 2023 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/15.0/legal/licenses.html).

from odoo import _, _lt, api, fields, models
from odoo.exceptions import ValidationError


class PrintProductLabelSection(models.Model):
    _name = "print.product.label.section"
    _description = 'Template Sections of Product Labels'
    _order = 'sequence'

    sequence = fields.Integer(default=100)
    template_id = fields.Many2one(
        comodel_name='print.product.label.template',
        string='Template',
        ondelete='cascade',
        required=True,
    )
    template_preview_html = fields.Html(compute='_compute_template_preview_html')
    preview = fields.Boolean(default=True)
    type = fields.Selection(
        selection=[
            ('text', 'Text'),
            ('field', 'Model Field'),
            ('price', 'Price'),
            ('promo_price', 'Promo Price'),
            ('multi_price', 'Multiple prices (by quantity)'),
            ('product_attributes', 'Product Attributes'),
            ('image', 'Image'),
        ],
        default='text',
        required=True,
    )
    value = fields.Char()
    value_format = fields.Char(string='Format', help='Format for date and digit fields.')
    image = fields.Binary(attachment=True)
    field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        string='Field',
        ondelete='cascade',
        domain="[('id', 'in', field_ids)]",
    )
    field_name = fields.Char(related='field_id.name')
    field_ids = fields.Many2many(
        comodel_name='ir.model.fields',
        string='Available Fields',
        help='Technical field for a domain',
        compute='_compute_field_ids',
    )
    field_ttype = fields.Selection(related='field_id.ttype')
    relation_model_id = fields.Many2one(
        comodel_name='ir.model',
        compute='_compute_relation_model_id',
    )
    relation_field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        help='The first level of the relation field. Allow you to select related fields'
             ' in case when you have chosen the "Field" with the type "many2one".',
    )
    relation_field_ttype = fields.Selection(
        related='relation_field_id.ttype',
        string="Relation Field Type",
    )
    nested_relation_model_id = fields.Many2one(
        comodel_name='ir.model',
        compute='_compute_nested_relation_model_id',
    )
    nested_relation_field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        help='The second level of relation field. Allow you to select related fields in '
             'case when you have chosen the "Relation Field" with the type "many2one".',
    )
    height = fields.Float(
        string='Height, mm', digits=(10, 2), help='Section Height in mm.',
    )
    width = fields.Float(digits=(10, 2), help='Section Width.')
    width_measure = fields.Selection(
        selection=[
            ('%', 'Percents'),
            ('mm', 'mm'),
        ],
        default='%',
        required=True,
    )
    position = fields.Selection(
        selection=[
            ('none', 'Full Width'),
            ('left', 'Left Side'),
            ('right', 'Right Side'),
        ],
        string='Float',
        default='none',
        required=True,
    )
    line_height = fields.Float(
        digits=(10, 2), default=1.0, help='Section Line Height Ratio.',
    )
    align = fields.Selection(
        selection=[
            ('center', 'Center'),
            ('left', 'Left'),
            ('right', 'Right'),
            ('justify', 'Justify'),
        ],
        default='center',
        required=True,
    )
    font_size = fields.Float(digits=(10, 2), default=12, required=True)
    font_size_measure = fields.Selection(
        selection=[('px', 'Pixels'), ('mm', 'mm')],
        string='Measure',
        default='px',
        required=True,
    )
    font_weight = fields.Selection(
        selection=[
            ('100', '100'),
            ('normal', 'normal'),
            ('bold', 'bold'),
            ('900', '900'),
        ],
        default='normal',
        required=True,
    )
    letter_spacing = fields.Float(digits=(10, 2), help='Space between letters, in mm.')
    text_decoration = fields.Selection(
        selection=[
            ('line-through', 'Line Through'),
            ('none', 'None'),
        ],
        default='none',
    )
    text_color = fields.Char(default='#000000')
    widget = fields.Selection(
        selection=[
            ('price', 'Price'),
            ('barcode', 'Barcode'),
            ('qr_code', 'QR code'),
            ('image', 'Image'),
        ],
    )
    with_product_attribute_name = fields.Boolean(
        string='With Attribute Name',
        help='Place a product attribute name before the attribute value on labels.',
    )
    shorten_url = fields.Boolean(
        string='Shorten URL',
        help='If the section value is a URL, you can short it with the Odoo internal '
             'link tracker to get a link like this one: https://your-domain/r/aBc.',
    )
    make_url_absolute = fields.Boolean(
        string='Absolute URL',
        help="If the section value is a URL, and it's a relative, you can make it "
             "absolute and add your base domain by activating this option.",
    )
    currency_position = fields.Selection(
        selection=[
            ('default', 'By default'),
            ('before', 'Before price'),
            ('after', 'After price'),
            ('none', 'Without currency code'),
        ],
        default='default',
        required=True,
    )
    multi_price_limit = fields.Integer(
        help='Specify the limit to restrict a number of prices.',
        default=10,
    )
    multi_price_order = fields.Selection(
        selection=[
            ('desc', 'In descending order'),
            ('asc', 'In ascending order'),
        ],
        string='Price Order',
        default='desc',
        required=True,
    )
    padding_top = fields.Float(digits=(10, 2), help='Page Right Padding, in mm.')
    padding_bottom = fields.Float(digits=(10, 2), help='Page Bottom Padding, in mm.')
    padding_left = fields.Float(digits=(10, 2), help='Page Left Padding, in mm.')
    padding_right = fields.Float(digits=(10, 2), help='Page Right Padding, in mm.')
    margin_top = fields.Float(digits=(10, 2), help='Page Right Margin, in mm.')
    margin_bottom = fields.Float(digits=(10, 2), help='Page Bottom Margin, in mm.')
    margin_left = fields.Float(digits=(10, 2), help='Page Left Margin, in mm.')
    margin_right = fields.Float(digits=(10, 2), help='Page Right Margin, in mm.')
    with_border_top = fields.Boolean(string="Border Top")
    with_border_bottom = fields.Boolean(string="Border Bottom")
    with_border_left = fields.Boolean(string="Border Left")
    with_border_right = fields.Boolean(string="Border Right")
    border_width = fields.Integer(default=1, help='Border Width, in px')
    with_background = fields.Boolean(string="Background")
    background_color = fields.Char(default='#BBBBBB')
    active = fields.Boolean(default=True)

    @api.constrains('height')
    def _check_height(self):
        for section in self:
            if not section.height:
                raise ValidationError(_('The section height must be set.'))

    @api.constrains('type', 'widget')
    def _check_widget_image(self):
        for section in self:
            if section.type != 'field' and section.widget == 'image':
                raise ValidationError(
                    _('You can use the widget "Image" only for the "Model Fields" '
                      'section types.'))

    @api.depends('type')
    def _compute_field_ids(self):
        for section in self:
            if section.type == 'field':
                domain = [
                    ('model', '=', 'print.product.label.line')
                ] + self._get_field_domain()
                available_fields = self.env['ir.model.fields'].search(domain)
                section.field_ids = [(6, 0, available_fields.ids)]
            else:
                section.field_ids = None

    @api.depends('type', 'field_id')
    def _compute_relation_model_id(self):
        for section in self:
            if section.type == 'field' \
                    and section.field_id.ttype in self.relation_field_types():
                section.relation_model_id = self.env['ir.model'].search([
                    ('model', '=', section.field_id.relation)])[:1].id
            else:
                section.relation_model_id = None

    @api.depends('type', 'field_id', 'relation_field_id')
    def _compute_nested_relation_model_id(self):
        for section in self:
            if (
                section.type == 'field'
                and section.field_id
                and section.field_id.ttype in self.relation_field_types()
                and section.relation_field_id
                and section.relation_field_id.ttype in self.relation_field_types()
            ):
                section.nested_relation_model_id = self.env['ir.model'].search([
                    ('model', '=', section.relation_field_id.relation),
                ])[:1].id
            else:
                section.nested_relation_model_id = None

    @api.depends('template_id')
    def _compute_template_preview_html(self):
        for section in self:
            section.template_preview_html = section.template_id.with_context(editable_section_id=section.id).preview_html  # flake8: noqa: E501

    @api.onchange('type')
    def _onchange_type(self):
        for section in self:
            if section.type != 'field':
                section.field_id = section.relation_field_id = section.nested_relation_field_id = False  # flake8: noqa: E501

    @api.onchange('field_id')
    def _onchange_field_id(self):
        for section in self:
            if section.relation_field_id.model_id != section.relation_model_id:
                section.relation_field_id = section.nested_relation_field_id = False

    @api.onchange('relation_field_id')
    def _onchange_relation_field_id(self):
        for section in self:
            if section.nested_relation_field_id.model_id != section.nested_relation_model_id:  # flake8: noqa: E501
                section.nested_relation_field_id = False

    @api.onchange('type', 'field_id', 'widget')
    def _onchange_widget(self):
        for section in self:
            # Reset the "Price" widget
            if section.widget == 'price' and section.field_id != self.env.ref(
                    'garazd_product_label_pro.field_print_product_label_line__price'):
                section.widget = False
            # Reset the value format
            section.value_format = False

    @api.model
    def binary_field_types(self):
        return ['binary']

    @api.model
    def text_field_types(self):
        return ['char', 'text', 'html', 'selection']

    @api.model
    def digit_field_types(self):
        return ['float', 'monetary', 'integer']

    @api.model
    def date_field_types(self):
        return ['date', 'datetime']

    @api.model
    def non_relation_field_types(self):
        return self.binary_field_types() + self.text_field_types() \
            + self.digit_field_types() + self.date_field_types()

    @api.model
    def relation_field_types(self):
        return ['many2one']

    @api.model
    def multi_relation_field_types(self):
        return ['many2many', 'one2many']

    @api.model
    def _get_field_domain(self):
        return [('ttype', 'in', self.non_relation_field_types() + self.relation_field_types())]  # flake8: noqa: E501

    @api.model_create_multi
    def create(self, vals_list):
        records = super(PrintProductLabelSection, self).create(vals_list)
        for section in records:
            template_sections = section.template_id.section_ids - section
            section['sequence'] = template_sections[-1].sequence + 1 \
                if template_sections else 100
        return records

    def get_float_position(self):
        self.ensure_one()
        width = 100 \
            if self.width_measure == '%' and self.width > 100 else self.width
        return "width: %(width).2f%(measure)s; float: %(float)s;" % {
            'width': width,
            'measure': self.width_measure,
            'float': self.position,
        }

    def get_border_style(self):
        self.ensure_one()
        border_style = ''
        for side in ['top', 'bottom', 'left', 'right']:
            if self['with_border_%s' % side]:
                border_style += 'border-%(side)s: %(width)dpx solid #000; ' % {
                    'side': side,
                    'width': self.border_width,
                }
        return border_style

    def get_background_style(self):
        self.ensure_one()
        bg_style = ''
        if self.with_background and self.background_color:
            bg_style += f'background-color: {self.background_color}; '
        return bg_style

    def get_html_style(self):
        self.ensure_one()
        style = "overflow: hidden; " \
                "height: %(height).2fmm; " \
                "padding: %(padding_top).2fmm %(padding_right).2fmm" \
                " %(padding_bottom).2fmm %(padding_left).2fmm; " \
                "margin: %(margin_top).2fmm %(margin_right).2fmm" \
                " %(margin_bottom).2fmm %(margin_left).2fmm; " \
                "text-align: %(align)s; " \
                "font-size: %(font_size)s; " \
                "color: %(text_color)s; " \
                "line-height: %(line_height).2f; " \
                "letter-spacing: %(letter_spacing).2fmm; " \
                "font-weight: %(font_weight)s; "\
                "text-decoration: %(text_decoration)s;" % {
                    'height': self.height,
                    'align': self.align,
                    'font_size': '%.2f%s' % (self.font_size, self.font_size_measure),
                    'text_color': self.text_color,
                    'line_height': self.line_height,
                    'letter_spacing': self.letter_spacing,
                    'font_weight': self.font_weight,
                    'padding_top': self.padding_top,
                    'padding_right': self.padding_right,
                    'padding_bottom': self.padding_bottom,
                    'padding_left': self.padding_left,
                    'margin_top': self.margin_top,
                    'margin_right': self.margin_right,
                    'margin_bottom': self.margin_bottom,
                    'margin_left': self.margin_left,
                    'text_decoration': self.text_decoration or 'none',
                }
        # Section width settings
        style += "clear: both;" if self.position == 'none' else self.get_float_position()
        # Section borders
        style += self.get_border_style()
        # Section background
        style += self.get_background_style()
        return style

    def _format_digit_value(self, value):
        self.ensure_one()
        return ('%s' % (self.value_format or '%s')) % value

    def _get_field_value(self, record, field) -> str:
        """Return a value of the "field" for the "record"."""
        self.ensure_one()
        section = self

        # Retrieving a value
        if field.ttype == 'selection':
            selection = record.fields_get([field.name])[field.name].get('selection', [])
            vals = dict(selection)
            value = vals.get(record[field.name])
        else:
            value = record[field.name]

        # Format empty values
        value = value if value is not False else ''

        # Format values for the digit and date fields
        if value and not section.widget:

            # Format values for the digit fields
            if field.ttype in self.digit_field_types():
                value = section._format_digit_value(value)

            # Format values for the date fields
            elif field.ttype in ['date', 'datetime']:
                lang = self.env['res.lang']._lang_get(self.env.lang) \
                    or self.env.ref('base.lang_en')
                value = value.strftime(section.value_format or lang.date_format)

        return value

    def _get_price_value(self, label, pricelist=False, min_quantity=1.0) -> str:
        self.ensure_one()
        section = self
        product = label.product_id
        if pricelist:
            price = pricelist._get_product_price(product, min_quantity)
        else:
            price = label.price
        value = section._format_digit_value(price)

        if section.currency_position != 'none':
            currency = pricelist.currency_id
            before = section.currency_position == 'before' or section.currency_position == 'default' and currency.position == 'before'  # flake8: noqa: E501
            if before:
                value = '%s %s' % (currency.symbol, value)
            else:
                value = '%s %s' % (value, currency.symbol)
        return value

    @api.model
    def get_pricelist_items(self, product, pricelist, sort_reverse=False):
        """Collect all pricelist rules that affect the current product."""
        price_rules = pricelist.item_ids.filtered(
            lambda l: l.product_id == product and l.min_quantity
        )
        price_rules |= pricelist.item_ids.filtered(
            lambda l: l.product_tmpl_id == product.product_tmpl_id
            and not l.product_id and l.min_quantity
        )
        price_rules |= self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist.id),
            ('categ_id', 'parent_of', product.categ_id.id),
            ('min_quantity', '!=', 0),
        ])
        # Remove rules with duplicated min quantity values
        res = self.env['product.pricelist.item'].browse()
        for rule in price_rules:
            if rule.min_quantity not in res.mapped('min_quantity'):
                res += rule
        return res.sorted('min_quantity', reverse=sort_reverse)

    @api.model
    def get_short_url(self, url: str, title: str) -> str:
        # Search a short link, if it exists
        link = self.env['link.tracker'].search([('url', '=', url if url.startswith('http') else f'http://{url}')])
        if not link:
            # Create a new short link, if it does not exist
            link = self.env['link.tracker'].create({
                'url': url,
                'title': title,
            })
        return link.short_url

    def get_value(self, label):
        """Return value for a section depending on label.
        :param label: record of "print.product.label.line" model
        :return: str
        """
        # flake8: noqa: E501
        # pylint: disable=too-many-branches
        self.ensure_one()
        section = self.sudo()  # Add sudo to allow users without "Administration/Access Rights" generate labels
        value = ''
        allowed_text_field_types = self.text_field_types() + self.digit_field_types() + self.date_field_types()
        allowed_relation_field_types = self.relation_field_types()

        # There are three relation levels:
        # Level 0 - the product label level
        # Level 1 - the level of relation field of the product label model
        # Level 2 - the level of relation field of the relation field

        if section.type == 'text':
            value = section.value or ''

        elif section.type == 'price':
            value = section._get_price_value(label, label.wizard_id.pricelist_id)

        elif section.type == 'promo_price' and label.wizard_id.sale_pricelist_id:
            value = section._get_price_value(label, label.wizard_id.sale_pricelist_id)

        elif section.type == 'multi_price' and label.wizard_id.pricelist_id:
            pricelist = label.wizard_id.pricelist_id
            qty_prices = []
            for pl_rule in self.get_pricelist_items(
                    label.product_id, pricelist,
                    sort_reverse=section.multi_price_order == 'asc',
            )[:section.multi_price_limit]:
                qty_prices.append({
                    'qty': pl_rule.min_quantity,
                    'amount': section._get_price_value(label, label.wizard_id.pricelist_id, min_quantity=pl_rule.min_quantity),
                    'currency': pricelist.currency_id.symbol,
                })
            value = qty_prices

        elif section.type == 'field' and section.field_id:  # pylint: disable=too-many-nested-blocks

            # Level 0
            # Text and digit fields
            if section.field_ttype in allowed_text_field_types:
                value = section._get_field_value(label, section.field_id)
            # Relation fields
            elif section.relation_field_id and section.field_id.ttype in allowed_relation_field_types:

                # Level 1
                record = label[section.field_id.name]
                if record:
                    # Text and digit fields of the relation field
                    if section.relation_field_ttype in allowed_text_field_types:
                        value = section._get_field_value(record, section.relation_field_id)

                    # Nested relation fields of the relation field
                    elif section.relation_field_ttype in allowed_relation_field_types:

                        # Level 2
                        nested_record = record[section.relation_field_id.name]
                        if nested_record:
                            # Text and digit fields of the relation field
                            if section.nested_relation_field_id.ttype in allowed_text_field_types:
                                value = section._get_field_value(
                                    nested_record, section.nested_relation_field_id
                                )

        # Make a URL an absolute, if it's relative
        if section.make_url_absolute and not value.startswith('http'):
            value = f"{section.get_base_url().rstrip('/')}{value}"

        if section.shorten_url and value and not self._context.get('preview_mode'):
            # Generate a shorten URL
            value = self.get_short_url(
                value,
                "%s - %s" % (section.template_id.name, section.display_name),
            )
        return value

    def get_image_url(self, label):
        """Return URL for a section binary field depending on label.
        :param label: record of "print.product.label.line" model
        :return: str
        """
        self.ensure_one()
        section = self.sudo()  # Add sudo to allow users without "Administration/Access Rights" generate labels
        res = ''
        if section.type != 'field' \
                or not section.relation_model_id \
                or not section.relation_field_id \
                or section.relation_field_id.ttype != 'binary':
            return res

        model_name = section.relation_model_id.model
        field_name = section.field_id.name
        record = label[field_name]
        relation_field_name = section.relation_field_id.name
        if record:
            res = '/web/image/%s/%d/%s' % (model_name, record.id, relation_field_name)
        return res

    def name_get(self):
        return [(rec.id, "%s%s" % (
            rec.type == 'text'
            and (rec.value and f"{_lt('Text:')} {rec.value}" or _lt('Blank'))
            or rec.type == 'price' and _lt('Price')
            or rec.type == 'promo_price' and _lt('Promo Price')
            or rec.type == 'multi_price' and _lt('Multiple prices (by qty)')
            or rec.type == 'product_attributes' and _lt('Product Attributes')
            or rec.type == 'image' and _lt('Image')
            or rec.type == 'field'
            and "%s %s" % (
                rec.field_id.field_description,
                rec.relation_field_id and rec.relation_field_id.field_description or '',
            ),
            rec.widget and (" (widget: %s)" % rec.widget) or '',
        )) for rec in self]
