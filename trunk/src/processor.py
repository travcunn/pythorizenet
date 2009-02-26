##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import httplib
import urllib
import md5

FIELD_DELIM = '|'
RESPONSE_CODES = {
    '1': 'approved',
    '2': 'declined',
    '3': 'error',
    '4': 'held for review'
}
TESTING_PREFIX = '(TESTMODE) '
AMEX = 'AMEX'
DISCOVER = 'Discover'
MASTERCARD = 'MasterCard'
VISA = 'Visa'
UNKNOWN_CARD_TYPE = 'Unknown'


def identifyCreditCardType(card_num, card_len):
    card_type = UNKNOWN_CARD_TYPE
    card_1_digit = card_num[0]
    card_2_digits = card_num[:2]
    card_4_digits = card_num[:4]

    # AMEX
    if (card_len == 15) and card_2_digits in ('34', '37'):
        card_type = AMEX

    # MASTERCARD, DISCOVER & VISA
    elif card_len == 16:
        # MASTERCARD
        if card_2_digits in ('51', '52', '53', '54', '55'):
            card_type = MASTERCARD

        # DISCOVER
        elif (card_4_digits == '6011') or (card_2_digits == '65'):
            card_type = DISCOVER

        # VISA
        elif (card_1_digit == '4'):
            card_type = VISA

    # VISA
    elif (card_len == 13) and (card_1_digit == '4'):
        card_type = VISA

    return card_type

class TransactionResult(object):
    def __init__(self, data, delim=FIELD_DELIM):
        fields = data.split(delim)
        self.response_code = fields[0]
        self.response = RESPONSE_CODES[self.response_code]
        self.response_reason_code = fields[2]
        self.response_reason = fields[3]
        if self.response_reason.startswith(TESTING_PREFIX):
            self.test = True
            self.response_reason = self.response_reason.replace(TESTING_PREFIX, '')
        else:
            self.test = False
        self.approval_code = fields[4]
        self.trans_id = fields[6]
        self.amount = fields[9]
        self.hash = fields[37]
        self.card_type = None

    def validateHash(self, login, salt):
        value = ''.join([salt, login, self.trans_id, self.amount])
        return self.hash.upper() == md5.new(value).hexdigest().upper()

class AuthorizeNetConnection(object):
    def __init__(self, server, login, key, salt=None, timeout=None):
        self.server = server
        self.login = login
        self.salt = salt
        self.timeout = timeout
        self.delimiter = FIELD_DELIM
        self.standard_fields = dict(
            x_login = login,
            x_tran_key = key,
            x_version = '3.1',
            x_delim_data = 'TRUE',
            x_delim_char = self.delimiter,
            x_relay_response = 'FALSE',
            x_method = 'CC',
            )

    def sendTransaction(self, **kwargs):
        # if the card number passed in is the "generate an error" card...
        if kwargs.get('card_num') == '4222222222222':
            # ... turn on test mode (that's the only time that card works)
            kwargs['test_request'] = 'TRUE'

        body = self.formatRequest(kwargs)

        if self.server.startswith('localhost:'):
            server, port = self.server.split(':')
            conn = httplib.HTTPConnection(server, port)
        else:
            conn = httplib.HTTPSConnection(self.server, timeout=self.timeout)
        conn.putrequest('POST', '/gateway/transact.dll')
        conn.putheader('content-type', 'application/x-www-form-urlencoded')
        conn.putheader('content-length', len(body))
        conn.endheaders()
        conn.send(body)

        response = conn.getresponse()
        fields = response.read().split(self.delimiter)
        result = TransactionResult(fields)

        if (self.salt is not None
        and not result.validateHash(self.login, self.salt)):
            raise ValueError('MD5 hash is not valid (trans_id = %r)'
                             % result.trans_id)

        return result

    def formatRequest(self, params):
        line_items = []
        if 'line_items' in params:
            line_items = params.pop('line_items')
        fields = dict(('x_'+key, value) for key, value in params.iteritems())
        fields.update(self.standard_fields)
        fields_pairs = fields.items()
        for item in line_items:
            fields_pairs.append(('x_line_item', '<|>'.join(item)))
        return urllib.urlencode(fields_pairs)

class Transaction(object):
    def __init__(self, server, login, key, salt=None, timeout=None):
        self.connection = AuthorizeNetConnection(server, login, key, salt, timeout)

    def authorize(self, **kwargs):
        if not isinstance(kwargs['amount'], basestring):
            raise ValueError('amount must be a string')
        result = self.connection.sendTransaction(type='AUTH_ONLY', **kwargs)
        # get the card_type
        card_num = kwargs.get('card_num')
        if card_num is not None and len(card_num) >= 4:
            result.card_type = identifyCreditCardType(card_num[:4], len(card_num))
        return result

    def captureAuthorized(self, **kwargs):
        return self.connection.sendTransaction(type='PRIOR_AUTH_CAPTURE', **kwargs)

    def credit(self, **kwargs):
        return self.connection.sendTransaction(type='CREDIT', **kwargs)

    def void(self, **kwargs):
        return self.connection.sendTransaction(type='VOID', **kwargs)

class Recurring(object):
    pass
