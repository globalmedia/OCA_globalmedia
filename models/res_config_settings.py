from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    infinitepay_handle = fields.Char(
        string="InfinitePay Handle",
        config_parameter='payment_infinitepay.infinitepay_handle',
    )
