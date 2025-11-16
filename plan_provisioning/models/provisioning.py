from odoo import models, fields

class SaasPlanTemplate(models.Model):
    _name = 'saas.plan.template'
    _description = 'Template por Plano'

    name = fields.Char(required=True)
    plan_id = fields.Many2one('saas.plan', required=True)
    module_names = fields.Text(help="Nomes técnicos de módulos, separadas por vírgula")
    notes = fields.Text()

class Contract(models.Model):
    _inherit = 'contract.contract'

    def action_activate_contract(self):
        res = super().action_activate_contract()
        for c in self:
            if c.saas_plan_id:
                template = self.env['saas.plan.template'].search([('plan_id', '=', c.saas_plan_id.id)], limit=1)
                if template:
                    c.message_post(body=f"Provisionar instância com módulos: {template.module_names}")
                    # Aqui, dispare um webhook/CI para:
                    # - criar DB do cliente
                    # - instalar módulos listados
                    # - configurar subdomínio e dbfilter
        return res
