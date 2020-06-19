import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-l10n-ukraine",
    description="Meta package for oca-l10n-ukraine Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-account_bank_statement_import_online_ua_pb_interpay',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
