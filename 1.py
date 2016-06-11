import socket
s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect(('127.0.0.1', 9999))
s.send('GET')
s.send(' http://127.0.0.1/hello.html')
s.send(' HTTP/1.1\r\n')
