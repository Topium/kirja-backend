import sys
import mysql.connector
from config import server_cnf, db_credentials
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

def connect():
    try:
        cnx = mysql.connector.connect(
            user=db_credentials['user'],
            password=db_credentials['password'],
            database=db_credentials['database']
            )
    except mysql.connector.Error as err:
        print(err)
        return None
    else:
        return cnx

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.path)
        match urlparse(self.path).path:
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
                params = parse_qs(urlparse(self.path).query)
                page = int(params['page'][0] if 'page' in params.keys() else 1)
                size = int(params['size'][0] if 'size' in params.keys() else 10)

                cnx = connect()
                with cnx.cursor() as cur:
                    cur.execute('SELECT COUNT(*) AS row_count FROM books;')
                    row_count = cur.fetchone()[0]
                query = 'SELECT * FROM books WHERE id >= %s LIMIT %s;'
                with cnx.cursor() as cur:
                    cur.execute(query, [(page - 1) * size, size])
                    rows = cur.fetchall()
                cnx.close()
                print(vars(cur))
                books = [{ k:v for (k,v) in zip([col for col in cur.column_names], row) } for row in rows]
                data = { 'page': page, 'size': size, 'total': row_count, 'data': books}

                self.send_response(200)
                self.send_header('content-type', 'application/json') 
                self.end_headers() 
                self.wfile.write(str(data).encode('utf8'))

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