from odoo import models, fields
import requests

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    infinitepay_pending = fields.Boolean(string="Pagamento InfinitePay Pendente", default=False)
    transaction_nsu = fields.Char(string="NSU da Transação")

    def _verificar_pagamentos_infinitepay(self):
        handle = self.env['ir.config_parameter'].sudo().get_param('infinitepay.handle')
        for pedido in self.search([('infinitepay_pending', '=', True)]):
            url = f"https://api.infinitepay.io/invoices/public/checkout/payment_check/{handle}"
            payload = {
                "transaction_nsu": pedido.transaction_nsu,
                "external_order_nsu": pedido.name,
                "slug": pedido.name
            }
            response = requests.post(url, json=payload)
            if response.ok and response.json().get("paid"):
                pedido.action_confirm()
                pedido.infinitepay_pending = False