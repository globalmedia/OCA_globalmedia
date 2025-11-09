{
    'name': 'Pagamento InfinitePay',
    'version': '1.0.5',
    'category': 'Website',
    'summary': 'Integração com InfinitePay Checkout',
    'author': 'GlobalMedia',
    'depends': ['website_sale'],
    'data': [
        'views/infinitepay_settings.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
    'application': False,
}
