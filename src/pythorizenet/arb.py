import datetime
from lxml import etree
from pythorizenet import AuthorizeNet, TYPE_CREDIT, HOST_PROD, HOST_TEST

UNIT_MONTH = 'months'
UNIT_DAYS = 'days'

PERIOD_ONGOING = 9999

PATH = '/xml/v1/request.api'
ANET_XMLNS = ' xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd"'

class RecurringResult(object):
    def __init__(self, data):
        root = etree.XML(data)
        messages = root.find('messages')
        self.resultCode = messages.find('resultCode').text
        self.code = messages.find('message/code').text
        self.reason = messages.find('message/text').text
        self.subscription_id = None
        subscription_id = root.find('subscriptionId')
        if root.tag == 'ARBCreateSubscriptionResponse' and subscription_id is not None:
            self.subscription_id = subscription_id.text

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

    def set_schedule(self, period=PERIOD_ONGOING, start=None, count=1, unit=UNIT_MONTH):
        if start is None:
            start = datetime.datetime.now()
        self.schedule = (start, period, count, unit)

    def set_amount(self, amount):
        self.amount = str(amount)

    def set_trial(self, trialPeriod, trialAmount):
        self.trial = (trialPeriod, str(trialAmount))

    def set_credit(self, card_num, card_exp):
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
        self.payment = (TYPE_CREDIT, (card_num, tuple(card_exp)))

    def set_customer(self, first_name, last_name, company=None, address=None, city=None, state=None, zip=None, country=None):
        self.customer = (first_name, last_name, company, address, city, state, zip, country)

    def set_subscription_id(self, subscription_id):
        self.subscription_id = subscription_id

    def _toXml(self, requestType):
        root = etree.Element(requestType, xmlns=ANET_XMLNS)
        auth = etree.SubElement(root, "merchantAuthentication")
        etree.SubElement(auth, "name").text = self.login
        etree.SubElement(auth, "transactionKey").text = self.key
        if self.subscription_id:
            etree.SubElement(root, 'subscriptionId').text = str(self.subscription_id)
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
        return RecurringResult(response)

    def create(self):
        xml = self._toXml('ARBCreateSubscriptionRequest')
        response = self.conn.send(xml)
        return self._fromXml(response)

    def update(self):
        xml = self._toXml('ARBUpdateSubscriptionRequest')
        response = self.conn.send(xml)
        return self._fromXml(response)

    def cancel(self):
        xml = self._toXml('ARBCancelSubscriptionRequest')
        response = self.conn.send(xml)
        return self._fromXml(response)

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print 'You must provide your login and trans id as parameters!'
        sys.exit()
    import pdb; pdb.set_trace()
    create = Recurring(HOST_PROD, sys.argv[1], sys.argv[2])
    create.set_schedule()
    create.set_amount('10.00')
    #create.add_credit('4427802718148774', ('2010', '03'))
    create.set_credit('4222222222222', ('2011', '03'))
    create.set_customer('john', 'smith')
    result = create.create()
    update = Recurring(HOST_PROD, sys.argv[1], sys.argv[2])
    update.set_subscription_id(result.subscription_id)
    update.set_amount('20.00')
    update.update()
    #cancel = Recurring(HOST_PROD, sys.argv[1], sys.argv[2])
    #cancel.add_subscription_id(result.subscription_id)
    #cancel.cancel()
