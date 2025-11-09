from odoo import http, _
from odoo.http import request
from datetime import datetime
import requests
import logging

_logger = logging.getLogger(__name__)

class InfinitePayController(http.Controller):

    @http.route(['/shop/infinitepay'], type='http', auth='public', website=True)
    def shop_infinitepay(self, **post):
        order = request.website.sale_get_order()
        if not order:
            return request.redirect('/shop')

        acquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'infinitepay')], limit=1)
        if not acquirer or not acquirer.infinitepay_handle:
            _logger.error("InfinitePay acquirer not configured or handle missing")
            return request.render('payment.payment_error', {'error': _('Pagamento indisponível no momento.')})

        # Create a payment.transaction record to keep idempotency and reconciliation
        tx = request.env['payment.transaction'].sudo().create({
            'acquirer_id': acquirer.id,
            'amount': order.amount_total,
            'currency_id': order.pricelist.currency_id.id,
            'reference': order.name,
            'partner_id': order.partner_id.id or False,
            'state': 'draft',
        })

        tx_vals = {
            'reference': tx.reference,
            'amount': float(tx.amount),
            'currency': tx.currency_id and tx.currency_id.name or None,
            'return_url': request.httprequest.host_url + 'payment/infinitepay/return',
            'items': [{'name': l.name, 'price': int(l.price_total * 100), 'quantity': int(l.product_uom_qty)} for l in order.order_line],
            'customer_name': order.partner_id.name if order.partner_id else None,
            'customer_email': order.partner_id.email if order.partner_id else None,
        }

        try:
            vals = acquirer.sudo().infinitepay_form_generate_values(tx_vals)
            payment_url = vals.get('payment_url')
            if not payment_url:
                _logger.error("InfinitePay: form_generate_values returned no payment_url for tx %s", tx.id)
                return request.render('payment.payment_error', {'error': _('Erro ao iniciar pagamento.')})
            # mark tx as pending before redirect to avoid race conditions
            tx.sudo().write({'state': 'pending'})
            return request.redirect(payment_url)
        except Exception as e:
            _logger.exception("Error generating InfinitePay payment URL: %s", e)
            return request.render('payment.payment_error', {'error': _('Erro ao iniciar pagamento.')})

    @http.route(['/payment/infinitepay/return'], type='http', auth='public', website=True)
    def infinitepay_return(self, **post):
        transaction_nsu = post.get('transaction_id') or post.get('transaction_nsu')
        external_order = post.get('order_nsu') or post.get('external_order_nsu') or post.get('slug')
        slug = post.get('slug') or external_order

        acquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'infinitepay')], limit=1)
        if not acquirer or not acquirer.infinitepay_handle:
            _logger.error("InfinitePay return called but acquirer not configured")
            return request.render('payment.payment_error', {'error': _('Configuração do gateway incorreta.')})

        if not external_order or not transaction_nsu:
            _logger.warning("InfinitePay return missing parameters: external_order=%s transaction_nsu=%s", external_order, transaction_nsu)
            return request.render('payment.payment_error', {'error': _('Dados do pagamento incompletos.')})

        # find transaction
        tx = request.env['payment.transaction'].sudo().search([
            ('reference', '=', external_order),
            ('acquirer_id', '=', acquirer.id)
        ], limit=1)

        # If transaction not found, log and still verify via payment_check to be safe
        if not tx:
            _logger.warning("InfinitePay return: payment.transaction not found for reference %s", external_order)

        # If tx exists and already processed, show confirmation
        if tx and tx.state in ('done', 'authorized'):
            order = request.env['sale.order'].sudo().search([('name', '=', external_order)], limit=1)
            return request.render('website_sale.confirmation', {'order': order})

        # Server-side call to payment_check to validate transaction
        try:
            url = f"https://api.infinitepay.io/invoices/public/checkout/payment_check/{acquirer.infinitepay_handle}"
            payload = {
                'transaction_nsu': transaction_nsu,
                'external_order_nsu': external_order,
                'slug': slug
            }
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            _logger.exception("InfinitePay payment_check request failed for order %s: %s", external_order, e)
            return request.render('payment.payment_error', {'error': _('Erro na verificação do pagamento.')})

        # Basic schema validation
        paid = bool(data.get('paid') is True)
        resp_amount = data.get('amount')  # may be None depending on API
        resp_currency = data.get('currency')  # may be None depending on API
        resp_tx_nsu = data.get('transaction_nsu') or data.get('transaction_id') or transaction_nsu
        resp_ref = data.get('external_order_nsu') or data.get('order_nsu') or external_order

        # Validate that returned transaction/order identifiers match
        if str(resp_tx_nsu) != str(transaction_nsu) or str(resp_ref) != str(external_order):
            _logger.error("InfinitePay verify mismatch ids: expected tx %s/ref %s got tx %s/ref %s", transaction_nsu, external_order, resp_tx_nsu, resp_ref)
            if tx:
                tx.sudo().write({'state': 'error'})
            return request.render('payment.payment_error', {'error': _('Dados do pagamento inválidos.')})

        # Validate amounts if API returned it
        if tx and resp_amount is not None:
            # Normalize possible centavos vs units: assume API returns integer cents OR float units.
            try:
                api_amount = float(resp_amount) / 100.0 if isinstance(resp_amount, int) and resp_amount > 1000 else float(resp_amount)
                if round(api_amount, 2) != round(float(tx.amount), 2):
                    _logger.error("InfinitePay amount mismatch for ref %s: tx.amount=%s api_amount=%s", external_order, tx.amount, api_amount)
                    tx.sudo().write({'state': 'error'})
                    return request.render('payment.payment_error', {'error': _('Valor do pagamento divergente.')})
            except Exception:
                _logger.exception("Error parsing amount from InfinitePay response for ref %s", external_order)
                tx.sudo().write({'state': 'error'})
                return request.render('payment.payment_error', {'error': _('Erro ao processar verificação.')})

        # Optionally validate currency
        if tx and resp_currency:
            try:
                if resp_currency.upper() != (tx.currency_id and tx.currency_id.name or '').upper():
                    _logger.error("InfinitePay currency mismatch for ref %s: tx.currency=%s api_currency=%s", external_order, tx.currency_id and tx.currency_id.name, resp_currency)
                    tx.sudo().write({'state': 'error'})
                    return request.render('payment.payment_error', {'error': _('Moeda incompatível.')})
            except Exception:
                _logger.exception("Error validating currency for ref %s", external_order)
                tx.sudo().write({'state': 'error'})
                return request.render('payment.payment_error', {'error': _('Erro ao processar verificação.')})

        # Final decision
        if paid:
            if tx:
                tx.sudo().write({
                    'state': 'done',
                    'acquirer_reference': transaction_nsu,
                    'date': datetime.now()
                })
            # Confirm related sale order if present
            order = request.env['sale.order'].sudo().search([('name', '=', external_order)], limit=1)
            if order and order.state in ('draft', 'sent'):
                try:
                    order.action_confirm()
                except Exception:
                    _logger.exception("Error confirming sale.order %s after InfinitePay paid", external_order)
            return request.render('website_sale.confirmation', {'order': order})
        else:
            if tx:
                tx.sudo().write({'state': 'cancel'})
            return request.render('payment.payment_error', {'error': _('Pagamento não confirmado.')})

    @http.route(['/payment/infinitepay/notify'], type='json', auth='public', methods=['POST'], csrf=False)
    def infinitepay_notify(self, **post):
        # Webhook: treat as advisory only; always verify via payment_check before finalizing
        data = request.jsonrequest
        external_order = data.get('external_order_nsu') or data.get('order_nsu') or data.get('slug')
        transaction_nsu = data.get('transaction_nsu') or data.get('transaction_id')
        acquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'infinitepay')], limit=1)
        if not acquirer or not external_order or not transaction_nsu:
            _logger.warning("InfinitePay notify missing acquirer/order/tx: %s", data)
            return {'status': 'ko'}

        # find transaction
        tx = request.env['payment.transaction'].sudo().search([('reference', '=', external_order), ('acquirer_id', '=', acquirer.id)], limit=1)
        # Double-check with payment_check before updating state
        try:
            url = f"https://api.infinitepay.io/invoices/public/checkout/payment_check/{acquirer.infinitepay_handle}"
            payload = {'transaction_nsu': transaction_nsu, 'external_order_nsu': external_order, 'slug': external_order}
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            data_chk = resp.json()
        except requests.RequestException as e:
            _logger.exception("InfinitePay notify: payment_check failed for %s: %s", external_order, e)
            return {'status': 'ko'}

        if not data_chk.get('paid'):
            if tx:
                tx.sudo().write({'state': 'cancel'})
            return {'status': 'cancelled'}

        # Paid according to payment_check
        if tx:
            tx.sudo().write({'state': 'done', 'acquirer_reference': transaction_nsu})
        order = request.env['sale.order'].sudo().search([('name', '=', external_order)], limit=1)
        if order and order.state in ('draft', 'sent'):
            try:
                order.action_confirm()
            except Exception:
                _logger.exception("Error confirming sale.order %s from notify", external_order)
        return {'status': 'ok'}
