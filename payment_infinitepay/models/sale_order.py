from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    infinitepay_pending = fields.Boolean(string='InfinitePay Pending', default=False)
    transaction_nsu = fields.Char(string='InfinitePay Transaction NSU')
    infinitepay_issue = fields.Boolean(string='InfinitePay Issue', default=False)
