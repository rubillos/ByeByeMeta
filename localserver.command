#!python

import os
from http.server import HTTPServer, CGIHTTPRequestHandler
import socket
path = '/Users/randy/Documents/Atom/Python/ByeByeMeta/Processed/'
print(f'Serving {path} at {socket.gethostname()}')
os.chdir(path)
server_object = HTTPServer(server_address=('', 80), RequestHandlerClass=CGIHTTPRequestHandler)
server_object.serve_forever()
