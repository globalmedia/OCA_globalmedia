from odoo import http
from odoo.http import request
import json
import urllib.parse
import requests

class InfinitePayController(http.Controller):

    def gerar_link_pagamento(self, order):
        handle = request.env['ir.config_parameter'].sudo().get_param('infinitepay.handle')
        items = [{
            "name": line.name,
            "price": int(line.price_total * 100),
            "quantity": int(line.product_uom_qty)
        } for line in order.order_line]

        params = {
            "items": json.dumps(items),
            "order_nsu": order.name,
            "redirect_url": request.httprequest.host_url + "payment/infinitepay/retorno"
        }

        base_url = f"https://checkout.infinitepay.io/{handle}"
        query_string = urllib.parse.urlencode(params)
        return f"{base_url}?{query_string}"

    def verificar_pagamento(self, transaction_nsu, external_order_nsu, slug):
        handle = request.env['ir.config_parameter'].sudo().get_param('infinitepay.handle')
        url = f"https://api.infinitepay.io/invoices/public/checkout/payment_check/{handle}"
        payload = {
            "transaction_nsu": transaction_nsu,
            "external_order_nsu": external_order_nsu,
            "slug": slug
        }
        response = requests.post(url, json=payload)
        if response.ok:
            return response.json().get("paid", False)
        return False

    @http.route('/shop/infinitepay', type='http', auth='public', website=True)
    def infinitepay_checkout(self, **kwargs):
        order = request.website.sale_get_order()
        order.infinitepay_pending = True
        link_pagamento = self.gerar_link_pagamento(order)
        return request.redirect(link_pagamento)

    @http.route('/payment/infinitepay/retorno', type='http', auth='public')
    def infinitepay_retorno(self, **kwargs):
        transaction_nsu = kwargs.get('transaction_id')
        external_order_nsu = kwargs.get('order_nsu')
        slug = kwargs.get('slug')

        if transaction_nsu and external_order_nsu and slug:
            pago = self.verificar_pagamento(transaction_nsu, external_order_nsu, slug)
            pedido = request.env['sale.order'].sudo().search([('name', '=', external_order_nsu)])
            if pedido and pago:
                pedido.action_confirm()
                pedido.infinitepay_pending = False
                pedido.transaction_nsu = transaction_nsu
                return request.render("website_sale.confirmation", {'order': pedido})
        return "Pagamento não confirmado ou dados inválidos."