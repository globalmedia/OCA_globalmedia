# plan_billing_bridge/models/billing.py
from odoo import models

class ContractSubscription(models.Model):
    _inherit = 'contract.subscription'

    def action_set_in_arrears(self):
        res = super().action_set_in_arrears()
        self.env['ir.config_parameter'].sudo().set_param('saas.readonly', '1')
        return res

    def action_set_in_progress(self):
        res = super().action_set_in_progress()
        self.env['ir.config_parameter'].sudo().set_param('saas.readonly', '0')
        return res
