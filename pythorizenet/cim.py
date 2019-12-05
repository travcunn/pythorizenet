#!/usr/bin/env python

from pythorizenet import AuthorizeNet, HOST_PROD, HOST_TEST
import http.client, urllib.request, urllib.parse, urllib.error

PATH = '/xml/v1/request.api'
ANET_XMLNS = ' xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd"'

VALIDATION_MODE_LIVE = 'liveMode'
VALIDATION_MODE_TEST = 'testMode'

class CustomerResult(object):
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

class Customer(object):
    def __init__(self, host, login, key):
        self.conn = AuthorizeNet(host, PATH, 'text/xml')
        self.login = login
        self.key = key
        self.payment = []
        self.billto = []
        self.shipping = []
        self.amount = None
        self.customer_id = None
        self.request_id = None
        self.validation_mode = 'none'

    def set_amount(self, amount):
        self.amount = str(amount)

    def add_payment(self, card_num, card_exp, card_code=None):
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
        self.payment.append((TYPE_CREDIT, (card_num, tuple(card_exp), card_code)))

    def add_billto(self, first_name, last_name, company=None, address=None, city=None, state=None, zip=None, country=None):
        self.billto.append((first_name, last_name, company, address, city, state, zip, country))

    def add_shipping(self, first_name, last_name, company=None, address=None, city=None, state=None, zip=None, country=None):
        self.shipping.append((first_name, last_name, company, address, city, state, zip, country))

    def set_customer_id(self, customer_id):
        self.customer_id = customer_id

    def set_profile_id(self, profile_id):
        self.profile_id = profile_id

    def set_request_id(self, request_id):
        self.request_id = request_id

    def set_validation_mode(self, validation_mode):
        self.validation_mode = validation_mode

    def _toXml(self, requestType):
        rootElem = etree.Element(requestType, xmlns=ANET_XMLNS)
        authElem = etree.SubElement(rootElem, "merchantAuthentication")
        etree.SubElement(authElem, "name").text = self.login
        etree.SubElement(authElem, "transactionKey").text = self.key
        if self.reference_id:
            etree.SubElement(rootElem, 'refId').text = str(self.reference_id)
        if self.profile_id:
            etree.SubElement(rootElem, 'customerProfileId').text = str(self.profile_id)
        if requestType == 'createCustomerProfileRequest':
            profileElem = etree.SubElement(rootElem, 'profile')
            if self.customer_id:
                etree.SubElement(profileElem, 'merchantCustomerId').text = str(self.customer_id)
            profileElem = etree.SubElement(profileElem, 'paymentProfiles')
        else:
            profileElem = etree.SubElement(profileElem, 'paymentProfile')
        if self.payment or self.billto:
            if self.billto:
                for first_name, last_name, company, address, city, state, zip, country in self.billto:
                    billToElem = etree.SubElement(profileElem, 'billTo')
                    etree.SubElement(billToElem, 'firstName').text = first_name
                    etree.SubElement(billToElem, 'lastName').text = last_name
                    if company:
                        etree.SubElement(billToElem, 'company').text = company
                    if address:
                        etree.SubElement(billToElem, 'address').text = address
                    if city:
                        etree.SubElement(billToElem, 'city').text = city
                    if state:
                        etree.SubElement(billToElem, 'state').text = state
                    if zip:
                        etree.SubElement(billToElem, 'zip').text = zip
                    if country:
                        etree.SubElement(billToElem, 'country').text = country
            if self.payment:
                for type, cc_info in self.payment:
                    if type == TYPE_CREDIT:
                        (card_num, card_exp, card_code) = cc_info
                        credit = etree.SubElement(etree.SubElement(profileElem, 'payment'), 'creditCard')
                        etree.SubElement(credit, 'cardNumber').text = card_num
                        etree.SubElement(credit, 'expirationDate').text = '%s-%s' % card_exp
                        if card_code:
                            etree.SubElement(credit, 'cardCode').text = card_code
        if self.shipping:
            for first_name, last_name, company, address, city, state, zip, country in self.shipping:
                if requestType == 'createCustomerProfileRequest':
                    shippingElem = etree.SubElement(profileElem, 'shipToList')
                else:
                    shippingElem = etree.SubElement(rootElem, 'address')
                etree.SubElement(shippingElem, 'firstName').text = first_name
                etree.SubElement(shippingElem, 'lastName').text = last_name
                if company:
                    etree.SubElement(shippingElem, 'company').text = company
                if address:
                    etree.SubElement(shippingElem, 'address').text = address
                if city:
                    etree.SubElement(shippingElem, 'city').text = city
                if state:
                    etree.SubElement(shippingElem, 'state').text = state
                if zip:
                    etree.SubElement(shippingElem, 'zip').text = zip
                if country:
                    etree.SubElement(shippingElem, 'country').text = country
        etree.subElement(rootElem, 'validationMode').text = str(self.validation_mode)
        return etree.tostring(root, xml_declaration=True, encoding='utf-8')

    def _fromXml(self, response):
        #TODO: investigate why etree will not parse this document when this namespace definition is intact.
        # for now just remove it :-)
        response = response.replace(ANET_XMLNS, '')
        return CustomerResult(response)

    def create(self):
        xml = self._toXml('createCustomerProfileRequest')
        response = self.conn.send(xml)
        return self._fromXml(response)

    def createPayment(self):
        xml = self._toXml('createCustomerPaymentProfileRequest')
        response = self.conn.send(xml)
        return self._fromXml(response)

    def createShipping(self):
        xml = self._toXml('createCustomerShippingAddressRequest')
        response = self.conn.send(xml)
        return self._fromXml(response)

    def createTransaction(self):
        xml = self._toXml('createCustomerProfileTransactionRequest')
        response = self.conn.send(xml)
        return self._fromXml(response)

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print('You must provide your login and trans id as parameters!')
        sys.exit()
    import pdb; pdb.set_trace()
    create = Customer(HOST_PROD, sys.argv[1], sys.argv[2])
