from odoo import models, fields

class Contract(models.Model):
    _inherit = 'contract.contract'

    saas_plan_id = fields.Many2one('saas.plan', string="Plano SaaS")

    def action_activate_contract(self):
        res = super().action_activate_contract()
        for c in self:
            if c.saas_plan_id:
                self.env['ir.config_parameter'].sudo().set_param('saas.plan_id', c.saas_plan_id.id)
        return res
