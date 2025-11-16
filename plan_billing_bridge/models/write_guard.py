from odoo import models
from odoo.exceptions import UserError

class SaasWriteGuard(models.AbstractModel):
    _name = 'saas.write.guard'
    _description = 'Bloqueia escrita quando instância está em modo leitura'

    def _ensure_writable(self):
        readonly = self.env['ir.config_parameter'].sudo().get_param('saas.readonly') == '1'
        if readonly:
            raise UserError("Sua assinatura está em atraso. A instância está em modo leitura.")

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def write(self, vals):
        self.env['saas.write.guard']._ensure_writable()
        return super().write(vals)

    @classmethod
    def create(cls, vals_list):
        cls.env['saas.write.guard']._ensure_writable()
        return super(SaleOrder, cls).create(vals_list)
