# Copyright 2019-2020 Brainbean Apps (https://brainbeanapps.com)
# Copyright 2020 CorporateHub (https://corporatehub.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from base64 import b64decode
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import itertools
import json
import hashlib
import ssl
from tempfile import NamedTemporaryFile
from pytz import timezone, utc
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

from odoo import api, models, _
from odoo.exceptions import UserError

UA_PB_INTERPAY_API_BASE = \
    'https://interpay.privatbank.ua/inter-pay-service/api'
UA_PB_TIMEZONE = timezone('Europe/Kiev')
UA_PB_TIMESTAMP_BASE = datetime(1970, 1, 1, tzinfo=UA_PB_TIMEZONE)


class OnlineBankStatementProviderUaPbInterpay(models.Model):
    _inherit = 'online.bank.statement.provider'

    @api.model
    def _get_available_services(self):
        return super()._get_available_services() + [
            ('ua_pb_interpay', 'InterPay.PrivatBank.ua'),
        ]

    @api.multi
    def _obtain_statement_data(self, date_since, date_until):
        self.ensure_one()
        if self.service != 'ua_pb_interpay':
            return super()._obtain_statement_data(
                date_since,
                date_until,
            )  # pragma: no cover

        if not self.account_number:
            raise UserError(_('Bank Account not linked or Account Number not set'))

        if date_since.tzinfo:
            date_since = date_since.astimezone(utc).replace(tzinfo=None)
        if date_until.tzinfo:
            date_until = date_until.astimezone(utc).replace(tzinfo=None)

        balance_start, balance_end = self._ua_pb_interpal_get_balance(
            date_since,
            date_until,
        )

        transactions = self._ua_pb_interpal_get_transactions(
            date_since,
            date_until,
        )
        if not transactions:
            return [], {
                'balance_start': balance_start,
                'balance_end_real': balance_end,
            }

        # Normalize transactions, sort by date, and get lines
        transactions = list(sorted(
            transactions,
            key=lambda transaction: self._ua_pb_interpay_get_transaction_date(
                transaction
            )
        ))
        lines = list(itertools.chain.from_iterable(map(
            lambda x: self._ua_pb_interpay_transaction_to_lines(x),
            transactions
        )))

        return lines, {
            'balance_start': balance_start,
            'balance_end_real': balance_end,
        }

    @api.model
    def _ua_pb_interpay_string(self, value):
        # NOTE: Decodes unicode entities (\uXXXX) as well
        return value.encode('utf-8').decode('utf-8')

    @api.model
    def _ua_pb_interpay_decimal(self, value):
        if isinstance(value, float):
            return Decimal(value)
        elif isinstance(value, Decimal):
            return value
        elif isinstance(value, str):
            value = self._ua_pb_interpay_string(value)
            return Decimal(value.replace(',', '.'))
        raise UserError(_('Cannot convert "%s" (%s) to decimal') % (
            value,
            type(value),
        ))

    @api.model
    def _ua_pb_interpay_preparse_transaction(self, transaction):
        fields = transaction['fields']
        if 'DATECREATE' in fields:
            fields['DATECREATE'] = (UA_PB_TIMESTAMP_BASE + timedelta(
                milliseconds=fields['DATECREATE'],
            )).astimezone(utc).replace(tzinfo=None)
        if 'REFILLDATE' in fields:
            fields['REFILLDATE'] = (UA_PB_TIMESTAMP_BASE + timedelta(
                milliseconds=fields['REFILLDATE'],
            )).astimezone(utc).replace(tzinfo=None)
        return transaction

    @api.model
    def _ua_pb_interpay_transaction_to_lines(self, transaction):
        fields = transaction['fields']
        name = self._ua_pb_interpay_get_transaction_description(transaction)
        amount = self._ua_pb_interpay_get_transaction_amount(transaction)
        date = self._ua_pb_interpay_get_transaction_date(transaction)
        payment_ref = self._ua_pb_interpay_get_transaction_ref(transaction)
        partner_account = self._ua_pb_interpay_get_partner_bank_account(
            transaction
        )
        unique_import_id = '%s-%s' % (
            payment_ref,
            int(date.timestamp()),
        )
        line = {
            'name': name,
            'amount': str(amount),
            'date': date,
            'unique_import_id': unique_import_id,
        }
        if 'CLIENTFIO' in fields:
            line.update({
                'partner_name': self._ua_pb_interpay_string(
                    fields['CLIENTFIO']
                ),
            })
        if partner_account:
            line.update({
                'account_number': partner_account,
            })
        return [line]

    @api.multi
    def _ua_pb_interpal_get_balance(self, since, until):
        self.ensure_one()

        one_day = relativedelta(days=1)

        data = self._ua_pb_interpay_retrieve('/payment/report', {
            'from': int(since.timestamp()) * 1000,
            'to': int(min(since + one_day, until).timestamp()) * 1000,
            'pagination': {
                'page': 0,
                'per': 1,
            },
        })
        balance_start = next(filter(
            lambda turnover: turnover['acc'] == self.account_number,
            data['accountTurnovers']
        ))['startBalance']

        data = self._ua_pb_interpay_retrieve('/payment/report', {
            'from': int(max(until - one_day, since).timestamp()) * 1000,
            'to': int(until.timestamp()) * 1000,
            'pagination': {
                'page': 0,
                'per': 1,
            },
        })
        balance_end = next(filter(
            lambda turnover: turnover['acc'] == self.account_number,
            data['accountTurnovers']
        ))['endBalance']

        return balance_start, balance_end

    @api.multi
    def _ua_pb_interpal_get_transactions(self, since, until):
        self.ensure_one()
        # NOTE: Not more than 30 days in a row
        # NOTE: start_date <= date <= end_date, thus check every transaction
        interval_step = relativedelta(days=30)
        assert since.tzinfo is None
        interval_start = since
        assert until.tzinfo is None
        transactions = []
        while interval_start < until:
            interval_end = min(interval_start + interval_step, until)
            request_interval_start = interval_start \
                .replace(tzinfo=utc) \
                .astimezone(UA_PB_TIMEZONE) \
                .replace(tzinfo=None)
            request_interval_end = interval_end \
                .replace(tzinfo=utc) \
                .astimezone(UA_PB_TIMEZONE) \
                .replace(tzinfo=None)
            page = 0
            total_pages = None
            while total_pages is None or page < total_pages:
                data = self._ua_pb_interpay_retrieve('/payment/report', {
                    'from': int(request_interval_start.timestamp()) * 1000,
                    'to': int(request_interval_end.timestamp()) * 1000,
                    'pagination': {
                        'page': page,
                        'per': 1000,
                    },
                })
                interval_transactions = map(
                    lambda transaction:
                    self._ua_pb_interpay_preparse_transaction(
                        transaction
                    ),
                    data['list']
                )
                transactions += list(filter(
                    lambda t: self._ua_pb_interpay_filter_transaction(
                        t,
                        interval_start,
                        interval_end
                    ),
                    interval_transactions
                ))
                transactions += interval_transactions
                total_pages = data['pagination'].get('total', 1)
                page += 1
            interval_start += interval_step
        return transactions

    @api.multi
    def _ua_pb_interpay_filter_transaction(
            self, transaction, interval_start, interval_end):
        self.ensure_one()
        fields = transaction['fields']

        if fields.get('STATE', 'SUCCESS') != 'SUCCESS':
            return False

        timestamp = self._ua_pb_interpay_get_transaction_date(transaction)
        if timestamp >= interval_end or timestamp < interval_start:
            return False

        if self._ua_pb_interpay_get_our_account_number(transaction) \
                != self.account_number:
            return False

        return True

    @api.multi
    def _ua_pb_interpay_get_transaction_date(self, transaction):
        self.ensure_one()
        fields = transaction['fields']

        # NOTE: CSV reports use this date, as well as filtering
        date = fields.get('DATECREATE')
        if date:
            return date

        date = fields.get('REFILLDATE')
        if date:
            return date

        raise UserError(_('Transaction has no date: %s') % (
            transaction,
        ))

    @api.multi
    def _ua_pb_interpay_get_transaction_description(self, transaction):
        self.ensure_one()
        fields = transaction['fields']

        description = fields.get('DESCRIPTION')
        if description:
            return self._ua_pb_interpay_string(description)

        description = fields.get('REFILLDESCR')
        if description:
            return self._ua_pb_interpay_string(description)

        raise UserError(_('Transaction has no description: %s') % (
            transaction,
        ))

    @api.multi
    def _ua_pb_interpay_get_transaction_ref(self, transaction):
        self.ensure_one()
        fields = transaction['fields']

        ref = fields.get('PAYMENTREF')
        if ref:
            return self._ua_pb_interpay_string(ref)

        ref = fields.get('REFILLREF')
        if ref:
            return self._ua_pb_interpay_string(ref)

        raise UserError(_('Transaction has no ref: %s') % (
            transaction,
        ))

    @api.multi
    def _ua_pb_interpay_get_transaction_amount(self, transaction):
        self.ensure_one()
        fields = transaction['fields']

        amount = fields.get('AMTDEBIT')
        if amount is not None:
            amount = self._ua_pb_interpay_decimal(amount)
            return amount.copy_abs().copy_negate()

        amount = fields.get('REFILLAMT')
        if amount is not None:
            amount = self._ua_pb_interpay_decimal(amount)
            return amount.copy_abs()

        raise UserError(_('Transaction amount not found: %s') % (
            transaction,
        ))

    @api.multi
    def _ua_pb_interpay_get_our_account_number(self, transaction):
        self.ensure_one()
        fields = transaction['fields']

        if 'REFILLCREDACC' in fields:
            return self._sanitize_bank_account_number(
                self._ua_pb_interpay_string(fields['REFILLCREDACC'])
            )

        if 'EXTACC' in fields:
            return self._sanitize_bank_account_number(
                self._ua_pb_interpay_string(fields['EXTACC'])
            )

        raise UserError(_('Transaction has no origin account: %s') % (
            transaction,
        ))

    @api.multi
    def _ua_pb_interpay_get_partner_bank_account(self, transaction):
        self.ensure_one()
        fields = transaction['fields']

        if 'REFILLDEBACC' in fields:
            return self._ua_pb_interpay_string(fields['REFILLDEBACC'])

        if 'ACC2600' in fields:
            return self._ua_pb_interpay_string(fields['ACC2600'])

        if 'CARD' in fields:
            return self._ua_pb_interpay_string(fields['CARD'])

        raise UserError(_('Transaction has recipient bank account: %s') % (
            transaction,
        ))

    @api.multi
    def _ua_pb_interpay_retrieve(self, endpoint, data=None, method='POST'):
        self.ensure_one()
        if endpoint[0] != '/':
            endpoint = '/' + endpoint
        if endpoint[-1] != '/':
            endpoint = endpoint + '/'

        api_base = self.api_base or UA_PB_INTERPAY_API_BASE
        url = api_base + endpoint + str(uuid4()) + '.json'

        if data:
            data = json.dumps(data).encode('utf-8')

        headers = {
            'Content-Type': 'application/json',
        }
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        with NamedTemporaryFile() as certificate_file:
            certificate_file.write(b64decode(self.certificate))
            context.load_cert_chain(
                certfile=certificate_file.name,
                password=self.passphrase,
            )

        authenticate_data = None
        try:
            request = Request(url, data, headers, method=method)
            with self._ua_pb_interpay_urlopen(request, context=context):
                raise UserError(_('Failed to perform handshake'))
        except HTTPError as e:
            if e.code != 401:
                raise e
            authenticate_data = e.headers['WWW-Authenticate']

        authenticate_data_parts = authenticate_data.partition(' ')
        if authenticate_data_parts[0] != 'Digest':
            raise UserError(_(
                'Unsupported authentication method: %s'
            ) % (authenticate_data_parts[0],))

        def decode_auth_component(component):
            component = component.partition('=')
            key = component[0].strip()
            value = component[2].strip()
            if value[0] == '"' and value[-1] == '"':
                value = value[1:-1]
            return (key, value)
        authenticate = dict(map(
            decode_auth_component,
            authenticate_data_parts[2].split(',')
        ))

        realm = authenticate.get('realm')
        if not realm:
            raise UserError(_('Authentication realm not specified'))
        nonce = authenticate.get('nonce')
        if not nonce:
            raise UserError(_('Authentication nonce not specified'))
        qop = authenticate.get('qop')

        algorithm = authenticate.get('algorithm')
        if not algorithm:
            raise UserError(_('Authentication algorithm not specified'))
        session_based = algorithm.endswith('-sess')
        if session_based:
            algorithm = algorithm[0:-5]
        algorithms = hashlib.algorithms_guaranteed | hashlib.algorithms_available
        if algorithm not in algorithms and '-' in algorithm:
            algorithm = algorithm.replace('-', '')
        if algorithm not in algorithms:
            algorithm = algorithm.lower()
        if algorithm not in algorithms:
            raise UserError(_(
                'Authentication algorithm not supported: %s'
            ) % (algorithm,))
        hasher = hashlib.new(algorithm)

        uri = urlparse(url).path

        authorization = dict(authenticate)
        authorization['username'] = self.username
        authorization['uri'] = uri
        if qop:
            if qop not in ['auth', 'auth-int']:
                raise UserError(_(
                    'Authentication qop not supported: %s'
                ) % (qop,))

            cnonce = uuid4().hex[0:16]
            nc = '00000001'

            authorization['qop'] = qop
            authorization['nc'] = nc
            authorization['cnonce'] = cnonce

            a1 = '%s:%s:%s' % (
                self.username,
                realm,
                self.password
            )
            if session_based:
                partial_a1_hasher = hasher.copy()
                partial_a1_hasher.update(a1.encode('utf-8'))
                a1 = '%s:%s:%s' % (
                    partial_a1_hasher.hexdigest(),
                    nonce,
                    cnonce,
                )
            a1_hasher = hasher.copy()
            a1_hasher.update(a1.encode('utf-8'))
            hashed_a1 = a1_hasher.hexdigest()

            a2 = '%s:%s' % (
                method,
                uri,
            )
            if qop == 'auth-int':
                partial_a2_hasher = hasher.copy()
                if data:
                    partial_a2_hasher.update(data)
                a2 = '%s:%s' % (
                    a2,
                    partial_a2_hasher.hexdigest(),
                )
            a2_hasher = hasher.copy()
            a2_hasher.update(a2.encode('utf-8'))
            hashed_a2 = a2_hasher.hexdigest()

            response = '%s:%s:%s:%s:%s:%s' % (
                hashed_a1,
                nonce,
                nc,
                cnonce,
                qop,
                hashed_a2,
            )
            response_hasher = hasher.copy()
            response_hasher.update(response.encode('utf-8'))
            hashed_response = response_hasher.hexdigest()
            authorization['response'] = hashed_response

        def encode_auth_component(item):
            key, value = item
            if isinstance(value, str):
                value = '"%s"' % (value,)
            return '%s=%s' % (
                key,
                value,
            )
        authorization_data = 'Digest ' + ', '.join(list(map(
            encode_auth_component,
            authorization.items()
        )))
        headers['Authorization'] = authorization_data

        request = Request(url, data, headers, method=method)
        with self._ua_pb_interpay_urlopen(request, context=context) \
                as response:
            content = response.read().decode(
                response.headers.get_content_charset()
            )
        content = json.loads(content, parse_float=Decimal)
        if 'code' in content:
            # NOTE: If error is "no data", simulate empty response
            if content['code'] in ['IP0184']:
                return {
                    'list': [],
                    'pagination': {
                        'total': 0,
                    },
                }
            raise UserError('%s: %s' % (
                content['code'],
                content.get('message', _('Unknown error')),
            ))
        return content

    def _ua_pb_interpay_urlopen(self, request, **kwargs):
        return urlopen(request, **kwargs)
