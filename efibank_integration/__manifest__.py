{
    'name': 'Efíbank Integration',
    'version': '2.1.0',
    'summary': 'Integração Odoo 18.0 com Efíbank (PIX e Boletos), webhook seguro, conciliação e botões na fatura',
    'author': 'J',
    'license': 'LGPL-3',
    'category': 'Accounting/Payment',
    'depends': [
        'account',
        # Compatível com OCA l10n_brazil; opcional torná-lo obrigatório:
        # 'l10n_br_base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/efi_settings.xml',
        'views/efi_payment_views.xml',
        'views/account_move_efi_views.xml',
    ],
    'installable': True,
    'application': False,
}