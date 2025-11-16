from odoo import api, models
from odoo.exceptions import UserError

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        self._check_user_limit(increase=len(vals_list))
        return super().create(vals_list)

    def write(self, vals):
        if 'active' in vals and vals['active']:
            self._check_user_limit(increase=len(self))
        return super().write(vals)

    def _check_user_limit(self, increase=1):
        plan = self.env['saas.plan.runtime']._current_plan()
        if not plan or not plan.max_users:
            return
        active_users = self.env['res.users'].search_count([('active', '=', True)])
        if active_users + increase > plan.max_users:
            raise UserError("Limite de usuários do seu plano foi atingido. Faça upgrade.")
