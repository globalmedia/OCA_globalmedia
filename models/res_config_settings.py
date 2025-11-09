from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    infinitepay_handle = fields.Char(string="InfinitePay Handle")

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param('infinitepay.handle', self.infinitepay_handle)

    def get_values(self):
        res = super().get_values()
        res.update({
            'infinitepay_handle': self.env['ir.config_parameter'].sudo().get_param('infinitepay.handle'),
        })
        return res