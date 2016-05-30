from twisted.internet.defer import Deferred, succeed
from twisted.internet.protocol import ClientFactory, ServerFactory, Protocol

class HttpClientProtocol(Protocol):
    rsp = ''

    count = 0
    def dataReceived(self, data):
        print 'HttpClientProtocol received data[%d]:%s' % (count, data)
        count += 1
        self.rsp += data
    
    def connectionLost(self, reason):
        self.rspReceived(self.rsp)

    def rspReceived(self, rsp):
        self.factory.rsp_finished(rsp)

class HttpClientFactory(ClientFactory):

    protocol = HttpClientProtocol

    def __init__(self):
        self.deferred = Deferred()

    def rsp_finished(self, rsp):
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
            d.callback(rsp)

    def clientConnectionFailed(self, connector, reason):
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
            d.errback(reason)

class ProxyProtocol(Protocol):

    req = ''
    def connectionMade(self):
        d = self.factory.service.get_rsp()
        d.addCallback(self.transport.write)
        d.addBoth(lambda r: self.transport.loseConnection())

    count = 0
    def dataReceived(self, data):
        print 'ProxyProtol received data[%d]:%s' % (count, data)
        count += 1
        self.req += data




class ProxyFactory(ServerFactory):

    protocol = ProxyProtocol

    def __init__(self, service):
        self.service = service

class ProxyService(object):

    rsp = ''
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def get_rsp(self):
        if self.rsp is not None:
            print 'using cached'
            return succeed(rsp)

        print 'fetching from server'
        factory = HttpClientFactory()
        factory.deferred.addCallback(self.set_poem)
        from twisted.internet import reactor
        reactor.connectTCP(self.host, self.port)
        return factory.deferred

    def set_rsp(self, rsp):
        self.rsp = rsp;
        return rsp

def main():
    server_addr = ('192.168.3.57', 80)
    service = ProxyService(sever_addr)
    factory = ProxyFactory(service)

    from twisted.internet import reactor

    port = reactor.listenTcp(0, factory)

    print 'Proxying %s on %s' % (server_addr, port.getHost())

    reactor.run()

if __name__ == '__main__':
    main()