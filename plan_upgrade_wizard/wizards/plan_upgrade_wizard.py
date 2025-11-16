from odoo import models, fields, api

class PlanUpgradeWizard(models.TransientModel):
    _name = 'plan.upgrade.wizard'
    _description = 'Troca de Plano'

    contract_id = fields.Many2one('contract.contract', required=True)
    new_plan_id = fields.Many2one('saas.plan', required=True)
    pro_rata_amount = fields.Monetary(currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    @api.onchange('new_plan_id')
    def _onchange_new_plan(self):
        if self.new_plan_id:
            self.pro_rata_amount = (self.new_plan_id.price_monthly or 0.0) * 0.5

    def action_confirm(self):
        self.ensure_one()
        self.contract_id.saas_plan_id = self.new_plan_id
        self.contract_id.message_post(body=f"Plano alterado para {self.new_plan_id.name}. Pró-rata: {self.pro_rata_amount}.")
