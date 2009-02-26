import httplib, urllib, datetime
from lxml import etree

UNIT_MONTH = 'month'
UNIT_DAYS = 'days'

TYPE_CREDIT = 'credit'

PERIOD_ONGOING = 9999

class AuthorizeNet(object):
    def __init__(self, url):
        self.url = url

    def send(self, data):
        pass

class Recurring(object):
    def __init__(self, url, login, key):
        connection = AuthorizeNet(url)
        self.login = login
        self.key = key
        self.schedule = None
        self.amount = None
        self.trialAmount = None
        self.payment = None
        self.customer = None
        self.subscription_id = None

    def add_schedule(self, period=PERIOD_ONGOING, start=None, count=1, trial=0, unit=UNIT_MONTH):
        if not start:
            start = datetime.datetime.now()
        total = period + trial
        self.schedule = (start, total, count, trial, unit)

    def add_amount(self, amount):
        if not isinstance(amount, str):
            raise Exception('You must provide the amount as a string!')
        self.amount = amount

    def add_trialAmount(self, trialAmount):
        if not isinstance(trialAmount, str):
            raise Exception('You must provide the trial amount as a string!')
        self.trialAmount = trialAmount

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
            (start, total, count, trial, unit) = self.schedule
            schedule = etree.SubElement(subscription, 'paymentSchedule')
            interval = etree.SubElement(schedule, 'interval')
            etree.SubElement(interval, 'length').text = str(count)
            etree.SubElement(interval, 'unit').text = str(unit)
            etree.SubElement(schedule, 'startDate').text = start.strftime('%Y-%m-%d')
            etree.SubElement(schedule, 'totalOccurrences').text = str(total)
            etree.SubElement(schedule, 'trialOccurrences').text = str(trial)
        if self.amount:
            etree.SubElement(root, 'amount').text = str(self.amount)
        if self.trialAmount:
            etree.SubElement(root, 'trialAmount').text = str(self.trialAmount)
        if self.payment:
            type = self.payment[0]
            if type == TYPE_CREDIT:
                (card_num, card_exp) = self.payment[1]
                payment = etree.SubElement(root, 'payment')
                credit = etree.SubElement(payment, 'creditCard')
                etree.SubElement(credit, 'cardNumber').text = card_num
                etree.SubElement(credit, 'cardExpiration').text = '%s-%s' % card_exp
        if self.customer:
            (first_name, last_name, company, address, city, state, zip, country) = self.customer
            customer = etree.SubElement(root, 'billTo')
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
            etree.SubElement(root, 'subscriptionId').text = self.subscription_id
        return etree.tostring(root, xml_declaration=True, encoding='utf-8')

    def _fromXml(self, response):
        pass

    def create(self):
        xml = self._toXml('ARBCreateSubscriptionRequest')
        response = self.connnection.send(xml)
        self.subscription_id = self._fromXml(response)

    def update(self):
        xml = self._toXml('ARBUpdateSubscriptionRequest')
        response = self.connnection.send(xml)
        self._fromXml(response)

    def cancel(self):
        xml = self._toXml('ARBCancelSubscriptionRequest')
        response = self.connnection.send(xml)
        self._fromXml(response)

if __name__ == '__main__':
    test = Recurring('https://blah.com/', 'test', 'test')
    test.add_schedule()
    test.add_amount('10.00')
    test.add_credit('1111111111111111', ('2010', '03'))
    test.add_customer('ben', 'timby')
    print test._toXml('ARBCreateSubscriptionRequest')