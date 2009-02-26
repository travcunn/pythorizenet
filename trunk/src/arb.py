import httplib, urllib, datetime
from lxml import etree

UNIT_MONTH = 'months'
UNIT_DAYS = 'days'

TYPE_CREDIT = 'credit'

PERIOD_ONGOING = 9999

HOST_PROD = 'api.authorize.net'
HOST_TEST = 'apitest.authorize.net'
PATH = '/xml/v1/request.api'
ANET_XMLNS = ' xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd"'

class AuthorizeNet(object):
    def __init__(self, host):
        self.host = host

    def send(self, data):
        conn = httplib.HTTPSConnection(self.host)
        conn.putrequest('POST', PATH)
        conn.putheader('content-type', 'text/xml')
        conn.putheader('content-length', len(data))
        conn.endheaders()
        conn.send(data)

        response = conn.getresponse()
        return response.read()

class Recurring(object):
    def __init__(self, host, login, key):
        self.conn = AuthorizeNet(host)
        self.login = login
        self.key = key
        self.schedule = None
        self.amount = None
        self.trial = None
        self.payment = None
        self.customer = None
        self.subscription_id = None

    def add_schedule(self, period=PERIOD_ONGOING, start=None, count=1, unit=UNIT_MONTH):
        if not start:
            start = datetime.datetime.now()
        self.schedule = (start, period, count, unit)

    def add_amount(self, amount):
        if not isinstance(amount, str):
            raise Exception('You must provide the amount as a string!')
        self.amount = amount

    def add_trial(self, trialPeriod, trialAmount):
        if not isinstance(trialAmount, str):
            raise Exception('You must provide the trial amount as a string!')
        self.trial = (trialPeriod, trialAmount)

    def add_credit(self, card_num, card_exp):
        if not isinstance(card_exp, (tuple, list)):
            raise Exception('card_exp must be a tuple or list!')
        if len(card_exp) != 2:
            raise Exception('card_exp must contain two items (year and month)!')
        if len(card_exp[0]) != 4:
            raise Exception('First item of card_exp must be year as YYYY!')
        if len(card_exp[1]) != 2:
            raise Exception('Second item of card_exp must be month as MM!')
        self.payment = (TYPE_CREDIT, (card_num, card_exp))

    def add_customer(self, first_name, last_name, company=None, address=None, city=None, state=None, zip=None, country=None):
        self.customer = (first_name, last_name, company, address, city, state, zip, country)

    def add_subscription_id(self, subscription_id):
        self.subscription_id = subscription_id

    def _toXml(self, requestType):
        root = etree.Element(requestType, xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd")
        auth = etree.SubElement(root, "merchantAuthentication")
        etree.SubElement(auth, "name").text = self.login
        etree.SubElement(auth, "transactionKey").text = self.key
        subscription = etree.SubElement(root, 'subscription')
        if self.schedule:
            (start, total, count, unit) = self.schedule
            schedule = etree.SubElement(subscription, 'paymentSchedule')
            interval = etree.SubElement(schedule, 'interval')
            etree.SubElement(interval, 'length').text = str(count)
            etree.SubElement(interval, 'unit').text = str(unit)
            etree.SubElement(schedule, 'startDate').text = start.strftime('%Y-%m-%d')
            if self.trial:
                total += self.trial[0]
                etree.SubElement(schedule, 'trialOccurrences').text = str(self.trial[0])
            etree.SubElement(schedule, 'totalOccurrences').text = str(total)
        if self.amount:
            etree.SubElement(subscription, 'amount').text = str(self.amount)
        if self.trial:
            etree.SubElement(subscription, 'trialAmount').text = str(self.trial[1])
        if self.payment:
            type = self.payment[0]
            if type == TYPE_CREDIT:
                (card_num, card_exp) = self.payment[1]
                payment = etree.SubElement(subscription, 'payment')
                credit = etree.SubElement(payment, 'creditCard')
                etree.SubElement(credit, 'cardNumber').text = card_num
                etree.SubElement(credit, 'expirationDate').text = '%s-%s' % card_exp
        if self.customer:
            (first_name, last_name, company, address, city, state, zip, country) = self.customer
            customer = etree.SubElement(subscription, 'billTo')
            etree.SubElement(customer, 'firstName').text = first_name
            etree.SubElement(customer, 'lastName').text = last_name
            if company:
                etree.SubElement(customer, 'company').text = company
            if address:
                etree.SubElement(customer, 'address').text = address
            if city:
                etree.SubElement(customer, 'city').text = city
            if state:
                etree.SubElement(customer, 'state').text = state
            if zip:
                etree.SubElement(customer, 'zip').text = zip
            if country:
                etree.SubElement(customer, 'country').text = country
        if self.subscription_id:
            etree.SubElement(subscription, 'subscriptionId').text = self.subscription_id
        return etree.tostring(root, xml_declaration=True, encoding='utf-8')

    def _fromXml(self, response):
        #TODO: investigate why etree will not parse this document when this namespace definition is intact.
        # for now just remove it :-)
        response = response.replace(ANET_XMLNS, '')
        root = etree.XML(response)

        messages = root.find('messages')
        result_code = messages.find('resultCode').text
        if result_code == 'Error':
            message = messages.find('message')
            raise Exception('%s - %s' % (message.find('code').text, message.find('text').text))
        if result_code == 'Ok':
            return root.find('subscriptionId').text

    def create(self):
        xml = self._toXml('ARBCreateSubscriptionRequest')
        response = self.conn.send(xml)
        self.subscription_id = self._fromXml(response)

    def update(self):
        xml = self._toXml('ARBUpdateSubscriptionRequest')
        response = self.conn.send(xml)
        self._fromXml(response)

    def cancel(self):
        xml = self._toXml('ARBCancelSubscriptionRequest')
        response = self.conn.send(xml)
        self._fromXml(response)

if __name__ == '__main__':
    import sys, pdb
    pdb.set_trace()
    test = Recurring(HOST_PROD, sys.argv[1], sys.argv[2])
    test.add_schedule()
    test.add_amount('10.00')
    test.add_credit('4427802718148774', ('2010', '03'))
    test.add_customer('john', 'smith')
    test.create()
    print test.subscription_id
