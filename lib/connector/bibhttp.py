import httplib

class BibHttps(object):
    '''
    classdocs
    '''
    conn = None
    hostname = None
    certfile = None
    port = None

    def __init__(self,hostname,certfile,port):
        '''
        Constructor
        '''
        self.hostname = hostname
        self.certfile = certfile
        self.port = port
        self.conn = httplib.HTTPSConnection(
            hostname,
            key_file = certfile,
            cert_file = certfile,
            port=port
        )

    def get(self,file):
        self.conn.putrequest('GET', file)
        self.conn.endheaders()
        resp = self.conn.getresponse()
        return resp

    def __unicode__(self):
        return self.hostname+":"+self.port
    
    def __str__(self):
        return repr(self.__unicode__())
    
def client(hostname,certfile,port):
    return BibHttps(hostname,certfile,port)
