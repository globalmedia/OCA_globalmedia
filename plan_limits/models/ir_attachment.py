from odoo import models, api
from odoo.exceptions import UserError

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model_create_multi
    def create(self, vals_list):
        plan = self.env['saas.plan.runtime']._current_plan()
        if plan and plan.max_storage_mb:
            used = self._storage_used_mb()
            new_size_mb = sum((v.get('file_size', 0) for v in vals_list)) / (1024 * 1024)
            if used + new_size_mb > plan.max_storage_mb:
                raise UserError("Limite de armazenamento atingido. Faça upgrade de plano.")
        return super().create(vals_list)

    def _storage_used_mb(self):
        self.env.cr.execute("SELECT COALESCE(SUM(file_size),0) FROM ir_attachment WHERE type='binary'")
        row = self.env.cr.fetchone()
        return (row[0] or 0) / (1024 * 1024)
