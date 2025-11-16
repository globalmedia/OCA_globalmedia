from odoo import models

class SaasPlanRuntime(models.AbstractModel):
    _name = 'saas.plan.runtime'
    _description = 'Helpers de plano em runtime'

    def _current_plan(self):
        pid = self.env['ir.config_parameter'].sudo().get_param('saas.plan_id')
        try:
            pid = int(pid) if pid else 0
        except Exception:
            pid = 0
        return self.env['saas.plan'].sudo().browse(pid) if pid else False
