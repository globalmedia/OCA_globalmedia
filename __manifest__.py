{
    'name': 'Payment InfinitePay (acquirer)',
    'version': '1.0.7',
    'category': 'Accounting/Payment',
    'summary': 'InfinitePay Checkout integration as payment acquirer',
    'author': 'GlobalMedia',
    'depends': ['payment', 'website_sale', 'sale'],
    'data': [
        'data/payment_infinitepay_data.xml',
        'views/payment_infinitepay_views.xml',
        'views/payment_infinitepay_templates.xml',
        'views/payment_infinitepay_assets.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'Apache License 2.0',
}
