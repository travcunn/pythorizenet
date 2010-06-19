import lxml
import httplib

try:
    from hashlib import md5
except ImportError:
    from md5 import new as md5

TYPE_CREDIT = 'credit'
HOST_PROD = 'api.authorize.net'
HOST_TEST = 'apitest.authorize.net'
AMEX = 'AMEX'
DISCOVER = 'Discover'
MASTERCARD = 'MasterCard'
VISA = 'Visa'
UNKNOWN_CARD_TYPE = 'Unknown'

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

def generate_hash(*args):
    """generate_hash(hash_key, trans_id, amount)"""
    m = md5()
    map(m.update, args)
    return m.hexdigest().upper()

class AuthorizeNet(object):
    def __init__(self, host, path, mime):
        self.host = host
        self.path = path
        self.mime = mime

    def send(self, data):
        conn = httplib.HTTPSConnection(self.host)
        conn.putrequest('POST', self.path)
        conn.putheader('content-type', self.mime)
        conn.putheader('content-length', len(data))
        conn.endheaders()
        conn.send(data)

        response = conn.getresponse()
        return response.read()
