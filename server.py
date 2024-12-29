import sys
from config import server_cnf
from http.server import HTTPServer, BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.path)
        match self.path:
            case '/':
                self.send_response(200)
                self.send_header('content-type', 'text/html') 
                self.end_headers() 
                self.wfile.write(b'Home')

            case '/favicon.ico':
                with open('book-32.png', 'rb') as f:
                    self.send_response(200)
                    self.send_header('content-type', 'image/png') 
                    self.end_headers() 
                    self.wfile.write(f.read())

            case '/books':
                self.send_response(200)
                self.send_header('content-type', 'text/html') 
                self.end_headers() 
                self.wfile.write(b'Books')
                
            case _:
                self.send_response(404)
                self.send_header('content-type', 'text/html') 
                self.end_headers() 
                self.wfile.write(b'Not found')

def runserver():
    httpd = HTTPServer(('', server_cnf['port']), handler)
    try:
        print('Käynnistetään palvelin portissa', server_cnf['port'])
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Suljetaan...')
        sys.exit()
    except Exception as e:
        print('Poikkeus', e)

runserver()