import datetime
from lxml import etree
from comm import AuthorizeNet

UNIT_MONTH = 'months'
UNIT_DAYS = 'days'

TYPE_CREDIT = 'credit'

PERIOD_ONGOING = 9999

HOST_PROD = 'api.authorize.net'
HOST_TEST = 'apitest.authorize.net'
PATH = '/xml/v1/request.api'
ANET_XMLNS = ' xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd"'

class Recurring(object):
    def __init__(self, host, login, key):
        self.conn = AuthorizeNet(host, PATH, 'text/xml')
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
        if self.subscription_id:
            etree.SubElement(root, 'subscriptionId').text = self.subscription_id
        if requestType != 'ARBCancelSubscriptionRequest':
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
        return etree.tostring(root, xml_declaration=True, encoding='utf-8')

    def _fromXml(self, response):
        #TODO: investigate why etree will not parse this document when this namespace definition is intact.
        # for now just remove it :-)
        response = response.replace(ANET_XMLNS, '')
        root = etree.XML(response)

        messages = root.find('messages')
        result_code = messages.find('resultCode').text
        if result_code == 'Error':
            code = messages.find('message/code')
            text = messages.find('message/text')
            raise Exception('%s - %s' % (code.text, text.text))
        if result_code == 'Ok':
            if root.tag == 'ARBCreateSubscriptionResponse':
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
    import sys
    if len(sys.argv) != 3:
        print 'You must provide your login and trans id as parameters!'
        sys.exit()
    import pdb; pdb.set_trace()
    create = Recurring(HOST_PROD, sys.argv[1], sys.argv[2])
    create.add_schedule()
    create.add_amount('10.00')
    #create.add_credit('4427802718148774', ('2010', '03'))
    create.add_credit('1879237823782377', ('2010', '03'))
    create.add_customer('john', 'smith')
    create.create()
    update = Recurring(HOST_PROD, sys.argv[1], sys.argv[2])
    update.add_subscription_id(create.subscription_id)
    update.add_amount('20.00')
    update.update()
    #cancel = Recurring(HOST_PROD, sys.argv[1], sys.argv[2])
    #cancel.add_subscription_id('3661311')
    #cancel.cancel()
