from odoo import models
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_efibank_create_or_open_payment(self):
        """Cria (se não existir) e abre o registro efibank.payment vinculado à fatura."""
        self.ensure_one()
        if self.move_type != 'out_invoice':
            raise UserError("A ação Efíbank está disponível apenas para faturas de clientes.")

        Payment = self.env['efibank.payment'].sudo()
        payment = Payment.search([('move_id', '=', self.id)], limit=1)
        if not payment:
            payment = Payment.create({
                'move_id': self.id,
                'name': self.name or f"Fatura {self.id}",
                'amount': self.amount_total,
            })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pagamento Efíbank',
            'res_model': 'efibank.payment',
            'view_mode': 'form',
            'res_id': payment.id,
            'target': 'current',
        }

    def action_efibank_generate_pix(self):
        """Atalho para criar/abrir e gerar PIX direto da fatura."""
        action = self.action_efibank_create_or_open_payment()
        payment = self.env['efibank.payment'].browse(action['res_id'])
        payment.create_pix_payment()
        return action

    def action_efibank_generate_boleto(self):
        """Atalho para criar/abrir e gerar boleto direto da fatura."""
        action = self.action_efibank_create_or_open_payment()
        payment = self.env['efibank.payment'].browse(action['res_id'])
        payment.create_boleto_payment()
        return action