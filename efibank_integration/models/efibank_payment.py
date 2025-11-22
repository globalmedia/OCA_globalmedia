from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import base64

class EfiBankPayment(models.Model):
    _name = 'efibank.payment'
    _description = 'Pagamentos Efíbank'
    _order = 'id desc'

    name = fields.Char(string="Descrição", required=True)
    txid = fields.Char(string="TXID Efíbank", index=True)
    move_id = fields.Many2one('account.move', string="Fatura vinculada",
                              domain=[('move_type', '=', 'out_invoice')])
    partner_id = fields.Many2one(related='move_id.partner_id', store=True)
    amount = fields.Monetary(string="Valor", currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('pending', 'Pendente'),
        ('paid', 'Pago'),
        ('cancelled', 'Cancelado')
    ], default='draft', index=True)

    # PIX
    pix_qr_code = fields.Text(string="PIX Copia-e-Colas")
    pix_qr_image = fields.Binary(string="QR Code (PNG)")

    # Boleto
    boleto_url = fields.Char(string="URL do Boleto")
    boleto_pdf = fields.Binary(string="PDF do Boleto")
    boleto_number = fields.Char(string="Nosso Número")

    # Logs
    last_error = fields.Text(string="Último erro da API")

    @api.onchange('move_id')
    def _onchange_move_id(self):
        if self.move_id:
            self.amount = self.move_id.amount_total
            self.currency_id = self.move_id.currency_id.id or self.env.company.currency_id.id
            self.name = self.move_id.name or f"Fatura {self.move_id.id}"

    # -----------------------
    # Compatibilidade OCA l10n_brazil (campos de parceiro)
    # -----------------------
    def _partner_brazil_doc(self, partner):
        """Retorna (tipo, documento) compatível com OCA l10n_brazil e fallback sem OCA."""
        def only_digits(s):
            return ''.join([c for c in (s or '') if c.isdigit()])

        cpf = getattr(partner, 'l10n_br_cpf', '') or getattr(partner, 'cpf', '')
        cnpj = getattr(partner, 'l10n_br_cnpj', '') or getattr(partner, 'cnpj', '')
        cnpj_cpf = getattr(partner, 'cnpj_cpf', '')

        if cnpj_cpf:
            doc = only_digits(cnpj_cpf)
            return ('cnpj' if len(doc) > 11 else 'cpf', doc)

        if cnpj:
            return ('cnpj', only_digits(cnpj))
        if cpf:
            return ('cpf', only_digits(cpf))

        vat = only_digits(partner.vat or '')
        if vat:
            return ('cnpj' if len(vat) > 11 else 'cpf', vat)
        return ('cpf', '')

    def _partner_brazil_address(self, partner):
        """Retorna dict de endereço compatível com l10n_br_base (OCA) e fallback."""
        street_name = getattr(partner, 'street_name', None) or partner.street or ''
        street_number = getattr(partner, 'street_number', None) or ''
        district = getattr(partner, 'district', None) or ''  # bairro
        city = partner.city or ''
        uf = partner.state_id.code or partner.state_id.name or ''
        cep = ''.join([c for c in (partner.zip or '') if c.isdigit()])
        complemento = partner.street2 or ''

        endereco = street_name
        if street_number:
            endereco = f"{endereco}, {street_number}"
        if complemento:
            endereco = f"{endereco} - {complemento}"
        if district:
            endereco = f"{endereco} - {district}"

        return {
            "endereco": endereco.strip(),
            "cidade": city,
            "uf": uf,
            "cep": cep,
        }

    def _partner_brazil_name(self, partner):
        legal_name = getattr(partner, 'legal_name', None)
        return legal_name or partner.name or ''

    # -----------------------
    # Config e OAuth
    # -----------------------
    def _get_efibank_config(self):
        ICP = self.env['ir.config_parameter'].sudo()
        client_id = ICP.get_param('efibank.client_id')
        client_secret = ICP.get_param('efibank.client_secret')
        pix_key = ICP.get_param('efibank.pix_key')
        base_url = ICP.get_param('efibank.base_url') or 'https://api.efipay.com.br'
        oauth_path = ICP.get_param('efibank.oauth_path') or '/oauth/token'
        if not client_id or not client_secret:
            raise UserError("Credenciais do Efíbank não configuradas. Vá em Configurações → Efíbank Integração.")
        if not pix_key:
            raise UserError("Chave PIX não configurada. Vá em Configurações → Efíbank Integração.")
        return {
            'client_id': client_id,
            'client_secret': client_secret,
            'pix_key': pix_key,
            'base_url': base_url.rstrip('/'),
            'oauth_url': base_url.rstrip('/') + oauth_path,
        }

    def _get_access_token(self):
        cfg = self._get_efibank_config()
        try:
            resp = requests.post(cfg['oauth_url'], json={
                'client_id': cfg['client_id'],
                'client_secret': cfg['client_secret'],
                'grant_type': 'client_credentials'
            }, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            token = data.get('access_token')
            if not token:
                raise ValueError("access_token ausente na resposta OAuth")
            return token
        except Exception as e:
            self.write({'last_error': str(e)})
            raise UserError("Falha ao obter token de acesso do Efíbank.")

    # -----------------------
    # PIX
    # -----------------------
    def create_pix_payment(self):
        """Gera um PIX para a fatura vinculada (Cob)."""
        for rec in self:
            if not rec.move_id:
                raise UserError("Vincule uma fatura antes de gerar PIX.")
            token = rec._get_access_token()
            cfg = rec._get_efibank_config()
            url = f"{cfg['base_url']}/v1/pix/cob"  # ajuste conforme seu endpoint oficial
            payload = {
                "calendario": {"expiracao": 3600},
                "valor": {"original": f"{rec.amount:.2f}"},
                "chave": cfg['pix_key'],
                "solicitacaoPagador": rec.name
            }
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            try:
                r = requests.post(url, json=payload, headers=headers, timeout=30)
                r.raise_for_status()
                data = r.json()
                updates = {
                    'txid': data.get('txid') or rec.txid,
                    'pix_qr_code': data.get('pixCopiaECola') or data.get('copiaECola'),
                    'state': 'pending',
                }
                qr_png_b64 = data.get('qr_png_base64') or data.get('qrCodeImage')  # opcional
                if qr_png_b64:
                    updates['pix_qr_image'] = qr_png_b64
                rec.write(updates)
            except Exception as e:
                rec.write({'last_error': str(e)})
                raise UserError("Erro ao criar cobrança PIX no Efíbank.")

    # -----------------------
    # Boletos
    # -----------------------
    def create_boleto_payment(self):
        """Gera boleto para a fatura vinculada, usando dados fiscal/endereço do parceiro (OCA)."""
        for rec in self:
            if not rec.move_id:
                raise UserError("Vincule uma fatura antes de gerar boleto.")
            token = rec._get_access_token()
            cfg = rec._get_efibank_config()
            url = f"{cfg['base_url']}/v1/cob/boletos"  # ajuste conforme seu endpoint oficial

            partner = rec.move_id.partner_id
            tipo_doc, documento = rec._partner_brazil_doc(partner)
            addr = rec._partner_brazil_address(partner)
            nome = rec._partner_brazil_name(partner)

            pagador = {
                "nome": nome,
                "cpf": documento if (tipo_doc == 'cpf') else "",
                "cnpj": documento if (tipo_doc == 'cnpj') else "",
                "email": partner.email or "",
                **addr,
            }

            payload = {
                "valor": f"{rec.amount:.2f}",
                "pagador": pagador,
                "dataVencimento": fields.Date.to_string(fields.Date.context_today(self)),
                "descricao": rec.name,
            }
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            try:
                r = requests.post(url, json=payload, headers=headers, timeout=30)
                r.raise_for_status()
                data = r.json()
                updates = {
                    'boleto_url': data.get("linkBoleto") or data.get("boletoLink"),
                    'boleto_number': data.get("nossoNumero") or data.get("boletoNumber"),
                    'state': 'pending',
                }
                if data.get("pdfBoleto"):
                    updates['boleto_pdf'] = data["pdfBoleto"]  # base64 esperado
                elif data.get("pdf_url"):
                    pdf_r = requests.get(data["pdf_url"], headers=headers, timeout=30)
                    if pdf_r.ok:
                        updates['boleto_pdf'] = base64.b64encode(pdf_r.content)
                rec.write(updates)
            except Exception as e:
                rec.write({'last_error': str(e)})
                raise UserError("Erro ao emitir boleto no Efíbank.")

    # -----------------------
    # Conciliação automática
    # -----------------------
    def mark_as_paid(self):
        """Cria um account.payment e reconcilia a fatura vinculada."""
        for rec in self:
            if not rec.move_id or rec.state != 'paid':
                continue
            if rec.move_id.payment_state == 'paid':
                continue

            company = rec.move_id.company_id
            bank_journal = self.env['account.journal'].search([
                ('type', '=', 'bank'),
                ('company_id', '=', company.id),
            ], limit=1)
            if not bank_journal:
                raise UserError("Crie um diário do tipo Banco para registrar o pagamento (na mesma empresa da fatura).")

            payment = self.env['account.payment'].create({
                'payment_type': 'inbound',
                'partner_id': rec.move_id.partner_id.id,
                'amount': rec.amount,
                'currency_id': rec.move_id.currency_id.id,
                'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                'journal_id': bank_journal.id,
            })
            payment.action_post()

            credit_lines = payment.move_id.line_ids.filtered(
                lambda l: l.credit > 0 and l.account_id.internal_type == 'receivable'
            )
            if not credit_lines:
                credit_lines = payment.move_id.line_ids.filtered(lambda l: l.credit > 0)
            if not credit_lines:
                raise UserError("Não foi possível localizar linha de crédito do pagamento para conciliação.")

            rec.move_id.js_assign_outstanding_line(credit_lines[0].id)