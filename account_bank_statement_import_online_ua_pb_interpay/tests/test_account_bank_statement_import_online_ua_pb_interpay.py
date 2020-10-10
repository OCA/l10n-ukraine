# Copyright 2019-2020 Brainbean Apps (https://brainbeanapps.com)
# Copyright 2020 CorporateHub (https://corporatehub.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import json
from unittest import mock

from odoo.tests import common
from odoo import fields

_module_ns = 'odoo.addons' \
    '.account_bank_statement_import_online_ua_pb_interpay'
_provider_class = (
    _module_ns
    + '.models.online_bank_statement_provider_ua_pb_interpay'
    + '.OnlineBankStatementProviderUaPbInterpay'
)


class TestAccountBankAccountStatementImportOnlineUaPbInterpay(
    common.TransactionCase
):

    def setUp(self):
        super().setUp()

        self.now = fields.Datetime.now()
        self.currency_eur = self.env.ref('base.EUR')
        self.currency_usd = self.env.ref('base.USD')
        self.main_partner = self.env.ref('base.main_partner')
        self.AccountJournal = self.env['account.journal']
        self.OnlineBankStatementProvider = self.env[
            'online.bank.statement.provider'
        ]
        self.AccountBankStatement = self.env['account.bank.statement']
        self.AccountBankStatementLine = self.env['account.bank.statement.line']
        self.ResPartnerBank = self.env['res.partner.bank']

    def test_empty_pull(self):
        bank_account = self.ResPartnerBank.create({
            'acc_number': '12345678910',
            'partner_id': self.main_partner.id,
        })
        journal = self.AccountJournal.create({
            'name': 'Bank',
            'type': 'bank',
            'code': 'BANK',
            'currency_id': self.currency_eur.id,
            'bank_statements_source': 'online',
            'online_bank_statement_provider': 'ua_pb_interpay',
            'bank_account_id': bank_account.id,
        })

        provider = journal.online_bank_statement_provider_id
        mocked_response = json.loads("""{
    "list": [],
    "pagination": {
        "page": 0,
        "per": 1000,
        "total": 1
    },
    "accountTurnovers": [
        {
            "acc": "12345678910",
            "ccy": "EUR",
            "startBalance": 0.0,
            "endBalance": 0.0
        }
    ]
}""", parse_float=Decimal)
        with mock.patch(
            _provider_class + '._ua_pb_interpay_retrieve',
            return_value=mocked_response,
        ):
            data = provider._obtain_statement_data(
                self.now - relativedelta(hours=1),
                self.now,
            )

        self.assertFalse(data[0])
        self.assertEqual(data[1], {
            'balance_start': 0.0,
            'balance_end_real': 0.0,
        })

    def test_pull(self):
        bank_account = self.ResPartnerBank.create({
            'acc_number': '19190000000000',
            'partner_id': self.main_partner.id,
        })
        journal = self.AccountJournal.create({
            'name': 'Bank',
            'type': 'bank',
            'code': 'BANK',
            'currency_id': self.currency_eur.id,
            'bank_statements_source': 'online',
            'online_bank_statement_provider': 'ua_pb_interpay',
            'account_number': '19190000000000',
            'bank_account_id': bank_account.id,
        })

        provider = journal.online_bank_statement_provider_id
        mocked_response = json.loads("""{
    "list": [
        {
            "fields": {
                "REFILLDATE": 1581577281760,
                "REFILLCREDACC": "19190000000000",
                "REFILLCCY": "EUR",
                "REFILLAMT": 12345.0,
                "REFILLREF": "REF",
                "REFILLDESCR": "DESCRIPTION",
                "REFILLDEBACC": "15000000000000"
            }
        },
        {
            "fields": {
                "PAYMENTREF": "P12345",
                "DATECREATE": 1581582645120,
                "ACC2600CCY": "EUR",
                "DATECHANGE": 1581582715706,
                "AMTDEBIT": 901.5,
                "EXTACCCCY": "EUR",
                "STATE": "SUCCESS",
                "ACC2600": "26000000000000",
                "DESCRIPTION": "DESCRIPTION",
                "ERRORCODE": "000000",
                "CLIENTFIO": "Petro PETRENKO",
                "EXTACC": "19190000000000",
                "CCYDEBIT": "EUR"
            }
        }
    ],
    "pagination": {
        "page": 0,
        "per": 1000,
        "total": 1
    },
    "accountTurnovers": [
        {
            "acc": "19190000000000",
            "ccy": "EUR",
            "startBalance": 10000.0,
            "endBalance": 21443.5
        }
    ]
}""", parse_float=Decimal)
        with mock.patch(
            _provider_class + '._ua_pb_interpay_retrieve',
            return_value=mocked_response,
        ):
            data = provider._obtain_statement_data(
                datetime(2020, 2, 12),
                datetime(2020, 2, 14),
            )

        self.assertEqual(len(data[0]), 2)
        self.assertEqual(data[0][0], {
            'account_number': '15000000000000',
            'date': datetime(2020, 2, 13, 4, 59, 21, 760000),
            'amount': '12345.0',
            'name': 'DESCRIPTION',
            'unique_import_id': 'REF-1581569961',
        })
        self.assertEqual(data[0][1], {
            'account_number': '26000000000000',
            'date': datetime(2020, 2, 13, 6, 28, 45, 120000),
            'amount': '-901.5',
            'name': 'DESCRIPTION',
            'partner_name': 'Petro PETRENKO',
            'unique_import_id': 'P12345-1581575325',
        })
        self.assertEqual(data[1], {
            'balance_start': 10000.0,
            'balance_end_real': 21443.5,
        })
