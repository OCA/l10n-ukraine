# Copyright 2019-2020 Brainbean Apps (https://brainbeanapps.com)
# Copyright 2019-2020 Dataplug (https://dataplug.io)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name':
        'Online Bank Statements: PrivatBank Ukraine (ПриватБанк Україна)'
        ' InterPay',
    'version': '12.0.1.0.0',
    'author':
        'Brainbean Apps, '
        'Dataplug, '
        'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-ukraine/',
    'license': 'AGPL-3',
    'category': 'Accounting',
    'summary': 'Online bank statements for InterPay.PrivatBank.ua',
    'depends': [
        'account_bank_statement_import_online',
    ],
    'data': [
        'views/online_bank_statement_provider.xml',
    ],
    'installable': True,
}
