from odoo import models, fields

class SaasPlan(models.Model):
    _name = 'saas.plan'
    _description = 'Plano SaaS'

    name = fields.Char(required=True)
    max_users = fields.Integer(default=5)
    max_storage_mb = fields.Integer(default=500)
    allowed_module_names = fields.Text(help="Nomes técnicos separados por vírgula")
    max_invoices_month = fields.Integer(default=0)  # 0 = sem limite
    price_monthly = fields.Float(string="Preço mensal")
    