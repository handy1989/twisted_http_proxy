from twisted.internet.defer import Deferred, succeed
from twisted.internet.protocol import ClientFactory, ServerFactory, Protocol

class HttpClientProtocol(Protocol):
    rsp = ''


    def connectionMade(self):
        print 'HttpClientProtocol, connectionMade'
        self.transport.write(self.factory.req)

    count = 0
    header = ''
    body = ''
    content_len = 0
    def dataReceived(self, data):
        print 'HttpClientProtocol received data[%d]:%s' % (self.count, data)
        self.count += 1
        if self.content_len == 0:
            self.rsp += data
            header_end = self.rsp.find('\r\n\r\n')
            if header_end:
                print 'header_end:', header_end
                self.header = self.rsp[0:header_end]
                print 'header:', self.header
                content_begin = self.header.find('Content-Length: ')
                content_end = self.header.find('\n', content_begin)
                content = self.header[content_begin:content_end]
                print 'content:', content
                self.content_len = int(content.split(' ')[1])
                self.body = self.rsp[header_end+4:]
                print 'body:', self.body
        else:
            self.body += data
        if len(self.body) >= self.content_len:
            self.factory.rsp_finished(self.header + '\r\n\r\n' + self.body)


    
    def connectionLost(self, reason): 
        self.rspReceived(self.rsp)

    def rspReceived(self, rsp):
        self.factory.rsp_finished(rsp)

class HttpClientFactory(ClientFactory):

    protocol = HttpClientProtocol

    def __init__(self, req):
        self.deferred = Deferred()
        self.req = req

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
        print 'connectionMade'

    count = 0
    def dataReceived(self, data):
        print 'ProxyProtol received data[%d]:%s' % (self.count, data)
        self.count += 1
        self.req += data
        first_line_end = data.find('\n')
        first_line = data[0:first_line_end]
        url = first_line.split(' ')[1]
        host_port = url.split('/')[2]
        print 'first line:', first_line
        print 'url:', url
        print 'host_port:', host_port
        try:
            host, port = host_port.split(':')
            port = int(port)
        except:
            host = host_port
            port = 80

        print 'host:', host, ' port:', port

        d = self.factory.service.get_rsp(host, port, self.req)
        d.addCallback(self.transport.write)
        d.addBoth(lambda r: self.transport.loseConnection())





class ProxyFactory(ServerFactory):

    protocol = ProxyProtocol

    def __init__(self, service):
        self.service = service

class ProxyService(object):

    rsp = None
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def get_rsp(self, host, port, req):
        if self.rsp is not None:
            print 'using cached:%s' % self.rsp
            return succeed(self.rsp)

        print 'fetching from server'
        factory = HttpClientFactory(req)
        factory.deferred.addCallback(self.set_rsp)
        from twisted.internet import reactor
        reactor.connectTCP(host, port, factory)
        return factory.deferred

    def set_rsp(self, rsp):
        self.rsp = rsp;
        return rsp

def main():
    server_addr = ('127.0.0.1', 80)
    service = ProxyService(*server_addr)
    factory = ProxyFactory(service)

    from twisted.internet import reactor

    port = reactor.listenTCP(9999, factory)

    print 'Proxying %s on %s' % (server_addr, port.getHost())

    reactor.run()

if __name__ == '__main__':
    main()