#!/usr/bin/env python

from com import AuthorizeNet
import httplib
import urllib

TYPE_CREDIT = 'credit'
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
HOST_PROD = 'secure.authorize.net'
HOST_TEST = 'test.authorize.net'

def identify_card_type(card_num):
    card_len = len(card_num)
    card_type = UNKNOWN_CARD_TYPE
    card_1_digit = card_num[0]
    card_2_digits = card_num[:2]
    card_4_digits = card_num[:4]
    if (card_len == 15) and card_2_digits in ('34', '37'):
        card_type = AMEX
    elif card_len == 16:
        if card_2_digits in ('51', '52', '53', '54', '55'):
            card_type = MASTERCARD
        elif (card_4_digits == '6011') or (card_2_digits == '65'):
            card_type = DISCOVER
        elif (card_1_digit == '4'):
            card_type = VISA
    elif (card_len == 13) and (card_1_digit == '4'):
        card_type = VISA
    return card_type

class TransactionResult(object):
    def __init__(self, data, delim=FIELD_DELIM):
        fields = data.split(delim)
        self.code = int(fields[0])
        self.type = RESPONSE_CODES[fields[0]]
        self.subcode = int(fields[2])
        self.reason = fields[3]
        if self.reason.startswith(TESTING_PREFIX):
            self.test = True
            self.reason = self.reason.replace(TESTING_PREFIX, '')
        else:
            self.test = False
        self.approval = fields[4]
        self.transaction_id = fields[6]
        self.amount = fields[9]
        self.hash = fields[37]
        self.card_type = None

    def validate(self, login, salt):
        value = ''.join([salt, login, self.transaction_id, self.amount])
        return self.hash.upper() == md5(value).hexdigest().upper()

class Transaction(object):
    class Options(object):
        pass

    def __init__(self, host, login, key):
        self.conn = AuthorizeNet(host, '/gateway/transact.dll', 'application/x-www-form-urlencoded')
        self.login = login
        self.key = key
        self.delimiter = FIELD_DELIM
        self.amount = None
        self.payment = None
        self.customer = None
        self.options = Transaction.Options()
        self.add_options()

    def add_amount(self, amount):
        if not isinstance(amount, str):
            raise Exception('You must provide the amount as a string!')
        self.amount = amount

    def add_credit(self, card_num, card_exp, card_code=None):
        if not isinstance(card_exp, (tuple, list)):
            raise Exception('card_exp must be a tuple or list!')
        if len(card_exp) != 2:
            raise Exception('card_exp must contain two items (year and month)!')
        if len(card_exp[0]) != 4:
            raise Exception('First item of card_exp must be year as YYYY!')
        if len(card_exp[1]) == 1:
            card_exp[1] = '0' + card_exp[1]
        elif len(card_exp[1]) > 2:
            raise Exception('Second item of card_exp must be month as MM!')
        self.payment = (TYPE_CREDIT, card_num, tuple(card_exp), card_code)

    def add_customer(self, first_name, last_name, company=None, address=None, city=None, state=None, zip=None):
        self.customer = (first_name, last_name, company, address, city, state, zip)

    def add_transaction(self, id):
        self.trans_id = id

    def add_options(self, is_test=False, require_ccv=False, require_avs=False, duplicate_window=None):
        setattr(self.options, 'is_test', is_test)
        setattr(self.options, 'require_ccv', require_ccv)
        setattr(self.options, 'require_avs', require_avs)
        setattr(self.options, 'duplicate_window', duplicate_window)

    def _toPost(self, requestType):
        post = {
            'x_login': self.login,
            'x_tran_key': self.key,
            'x_version': '3.1',
            'x_type': requestType,
            'x_recurring_billing': 'NO',
            'x_delim_data': 'TRUE',
            'x_delim_char': self.delimiter,
            'x_relay_response': 'FALSE',
        }
        if self.amount:
            post['x_amount'] = self.amount
        if self.payment:
            if self.payment[0] == TYPE_CREDIT:
                post['x_method'] = 'CC'
            type, card_num, exp_date, ccv = self.payment
            post.update(
                {
                    'x_card_num': card_num,
                    'x_exp_date': '%s-%s' % exp_date
                }
            )
            if self.options.require_ccv:
                if not ccv:
                    raise Exception('CCV required by options but not provided!')
                post['x_card_code'] = ccv
        if self.options.is_test:
            post['x_test_request'] = 'YES'
        if self.options.duplicate_window is not None:
            post['x_duplicate_window'] = str(self.options.duplicate_window)
        if requestType in ('CREDIT', 'PRIOR_AUTH_CAPTURE', 'VOID'):
            if not self.trans_id:
                raise Exception('You must provide a trans_id for %s transactions!' % requestType)
            post['x_trans_id'] = self.trans_id
        if self.customer:
            (first_name, last_name, company, address, city, state, zip) = self.customer
            post['x_first_name'] = first_name
            post['x_last_name'] = last_name
            if self.options.require_avs:
                if not (address and city and state and zip):
                    raise Exception('AVS required by options but no customer data provided!')
                if company:
                    post['x_company'] = company
                if address:
                    post['x_address'] = address
                if city:
                    post['x_city'] = city
                if state:
                    post['x_state'] = state
                if zip:
                    post['x_zip'] = zip
        for name, value in post.items():
            post[name] = value.encode('utf-8')
        return urllib.urlencode(post)

    def _fromPost(self, data):
        return TransactionResult(data, self.delimiter)

    def authorize(self):
        data = self._toPost('AUTH_ONLY')
        response = self.conn.send(data)
        return self._fromPost(response)

    def capture(self):
        data = self._toPost('PRIOR_AUTH_CAPTURE')
        response = self.conn.send(data)
        return self._fromPost(response)

    def auth_capture(self):
        data = self._toPost('AUTH_CAPTURE')
        response = self.conn.send(data)
        return self._fromPost(response)

    def credit(self):
        pass

    def void(self):
        data = self._toPost('VOID')
        response = self.conn.send(data)
        return self._fromPost(response)

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print 'You must provide your login and trans id as parameters!'
        sys.exit()
    import pdb; pdb.set_trace()
    trans = Transaction(HOST_PROD, sys.argv[1], sys.argv[2])
    trans.add_options(is_test=True)
    trans.add_amount('1.00')
    trans.add_credit('4222222222222', ('2010', '03'))
    trans.add_customer('john', u'Bolidenv\xe4gen')
    result = trans.authorize()
    void = Transaction(HOST_PROD, sys.argv[1], sys.argv[2])
    void.add_transaction(result.transaction_id)
    result = void.void()
    
