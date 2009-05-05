import httplib

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