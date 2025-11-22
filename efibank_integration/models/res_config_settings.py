from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    efibank_client_id = fields.Char(string="Efíbank Client ID")
    efibank_client_secret = fields.Char(string="Efíbank Client Secret")
    efibank_pix_key = fields.Char(string="Chave PIX (e-mail, telefone ou chave aleatória)")
    efibank_base_url = fields.Char(string="Efíbank API Base URL", default="https://api.efipay.com.br")
    efibank_oauth_path = fields.Char(string="OAuth Path", default="/oauth/token")
    efibank_webhook_secret = fields.Char(string="Webhook Secret")

    def set_values(self):
        super().set_values()
        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_param('efibank.client_id', self.efibank_client_id or '')
        ICP.set_param('efibank.client_secret', self.efibank_client_secret or '')
        ICP.set_param('efibank.pix_key', self.efibank_pix_key or '')
        ICP.set_param('efibank.base_url', self.efibank_base_url or '')
        ICP.set_param('efibank.oauth_path', self.efibank_oauth_path or '')
        ICP.set_param('efibank.webhook_secret', self.efibank_webhook_secret or '')

    def get_values(self):
        res = super().get_values()
        ICP = self.env['ir.config_parameter'].sudo()
        res.update(
            efibank_client_id=ICP.get_param('efibank.client_id', default=''),
            efibank_client_secret=ICP.get_param('efibank.client_secret', default=''),
            efibank_pix_key=ICP.get_param('efibank.pix_key', default=''),
            efibank_base_url=ICP.get_param('efibank.base_url', default='https://api.efipay.com.br'),
            efibank_oauth_path=ICP.get_param('efibank.oauth_path', default='/oauth/token'),
            efibank_webhook_secret=ICP.get_param('efibank.webhook_secret', default=''),
        )
        return res