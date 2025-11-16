from odoo import models
from odoo.exceptions import UserError

class IrModuleModule(models.Model):
    _inherit = 'ir.module.module'

    def button_immediate_install(self):
        plan = self.env['saas.plan.runtime']._current_plan()
        if plan and plan.allowed_module_names:
            allowed = {m.strip() for m in plan.allowed_module_names.split(',') if m.strip()}
            disallowed = [m.name for m in self if m.name not in allowed]
            if disallowed:
                raise UserError("Módulos não permitidos pelo seu plano: %s" % ", ".join(disallowed))
        return super().button_immediate_install()
