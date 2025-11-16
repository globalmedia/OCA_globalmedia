from odoo import models, fields

class SaasUsage(models.Model):
    _name = 'saas.usage'
    _description = 'Uso por instância'

    users_active = fields.Integer(compute='_compute_users', store=False)
    storage_mb = fields.Float(compute='_compute_storage', store=False)
    invoices_month = fields.Integer(compute='_compute_invoices', store=False)

    def _compute_users(self):
        for rec in self:
            rec.users_active = self.env['res.users'].search_count([('active', '=', True)])

    def _compute_storage(self):
        for rec in self:
            self.env.cr.execute("SELECT COALESCE(SUM(file_size),0) FROM ir_attachment WHERE type='binary'")
            row = self.env.cr.fetchone()
            rec.storage_mb = (row[0] or 0) / (1024 * 1024)

    def _compute_invoices(self):
        for rec in self:
            today = fields.Date.today()
            start_month = fields.Date.start_of(today, 'month')
            rec.invoices_month = self.env['account.move'].search_count([
                ('move_type', 'in', ['out_invoice', 'in_invoice']),
                ('invoice_date', '>=', start_month),
            ])
