from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    infinitepay_pending = fields.Boolean(string='InfinitePay Pending', default=False)
    transaction_nsu = fields.Char(string='InfinitePay Transaction NSU')

    def action_infinitepay_mark_pending(self, transaction_nsu=None):
        for order in self:
            order.infinitepay_pending = True
            if transaction_nsu:
                order.transaction_nsu = transaction_nsu
