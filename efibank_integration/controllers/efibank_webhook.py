from odoo import http
from odoo.http import request

class EfiBankWebhookController(http.Controller):
    @http.route('/efibank/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def efi_webhook(self):
        """Recebe notificações do Efíbank (Efí Pay) com validação de segredo."""
        secret_config = request.env['ir.config_parameter'].sudo().get_param('efi.webhook_secret')
        provided_secret = request.httprequest.headers.get('X-EFI-Webhook-Secret')

        if not secret_config or provided_secret != secret_config:
            return {"success": False, "error": "Webhook não autorizado"}

        data = request.jsonrequest or {}
        txid = data.get("txid")
        status = data.get("status")

        if not txid:
            return {"success": False, "error": "txid ausente"}

        payment = request.env['efi.payment'].sudo().search([('txid', '=', txid)], limit=1)
        if not payment:
            payment = request.env['efi.payment'].sudo().search([('name', '=', txid)], limit=1)

        if not payment:
            return {"success": False, "error": "Pagamento não encontrado"}

        # Ajuste os status conforme retorno da sua API Efí (CONCLUIDA/LIQUIDADO/etc)
        if status in ["CONCLUIDA", "LIQUIDADO", "PAID", "paid"]:
            payment.write({'state': 'paid'})
            payment.mark_as_paid()
        elif status in ["REMOVIDA_PELO_USUARIO_RECEBEDOR", "CANCELADO", "cancelled"]:
            payment.write({'state': 'cancelled'})

        return {"success": True}