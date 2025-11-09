from odoo import models, fields, api
import json
import urllib.parse
import logging

_logger = logging.getLogger(__name__)

class PaymentAcquirerInfinitepay(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('infinitepay', 'InfinitePay')], ondelete={'infinitepay': 'set default'})
    infinitepay_handle = fields.Char(string='InfinitePay Handle', help='Handle fornecido pelo InfinitePay (usado na URL do checkout)')

    @api.model
    def _get_infinitepay_urls(self):
        return {
            'infinitepay_form_url': 'https://checkout.infinitepay.io/',
            'infinitepay_api_check': 'https://api.infinitepay.io/invoices/public/checkout/payment_check/',
        }

    def infinitepay_form_generate_values(self, tx_values):
        self.ensure_one()
        handle = (self.infinitepay_handle or '').strip()
        if not handle:
            _logger.error("InfinitePay acquirer called without handle configured")
            return {}

        base_url = self._get_infinitepay_urls()['infinitepay_form_url']
        params = {
            'items': json.dumps(tx_values.get('items', [])),
            'order_nsu': tx_values.get('reference'),
            'redirect_url': tx_values.get('return_url'),
        }

        # Add optional customer fields if present
        for k in ('customer_name', 'customer_email', 'customer_cellphone', 'address_cep', 'address_number', 'address_complement'):
            if tx_values.get(k):
                params[k] = tx_values.get(k)

        query = urllib.parse.urlencode(params)
        pay_url = f"{base_url}{handle}?{query}"
        return {
            'payment_url': pay_url
        }

    def _get_tx_from_notification(self, data):
        reference = data.get('external_order_nsu') or data.get('order_nsu')
        return self.env['payment.transaction'].search([('reference', '=', reference), ('acquirer_id', '=', self.id)], limit=1)
