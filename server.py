import sys
import cgi
import requests
import json
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
    
def verify_isbn(isbn):
    if len(isbn) == 10:
        check = 0
        for (i, d) in enumerate(isbn[0:-1]):
            check += (10-i) * int(d)
        check = check % 11
        check = 11 - check
        check = check % 11
        return isbn[-1] == str(check) or (isbn[-1] == 'X' and check == 10)
    elif len(isbn) == 13:
        check = 0
        for (i, d) in enumerate(isbn[0:-1]):
            mult = 1 if i % 2 == 0 else 3
            check += mult * int(d)
        check = check % 10
        check = 10 - check
        return isbn[-1] == str(check)
    else:
        return False

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
                self.wfile.write(json.dumps(data).encode('utf8'))

            case _:
                self.send_response(404)
                self.send_header('content-type', 'application/json') 
                self.end_headers() 
                self.wfile.write('{"error": "Ei endpointtia"}'.encode('utf8'))

    def do_POST(self):
        match urlparse(self.path).path:
            case '/books':
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST',
                            'CONTENT_TYPE': self.headers['Content-Type'],
                            }
                )
                isbn = form.getvalue('isbn')

                if not verify_isbn(isbn):
                    self.send_response(404)
                    self.send_header('content-type', 'application/json') 
                    self.end_headers() 
                    self.wfile.write('{"error": "ISBN ei validi"}'.encode('utf8'))

                else:
                    print('isbn', isbn)
                    url = 'https://api.finna.fi/api/v1/search?lookfor={}&type=AllFields&field%5B%5D=title&field%5B%5D=year&field%5B%5D=nonPresenterAuthors&page=1&limit=20'.format(isbn)
                    r = requests.get(url)
                    res = r.json()
                    print('res', res)
                    
                    if res['resultCount'] < 1:
                        self.send_response(404)
                        self.send_header('content-type', 'application/json') 
                        self.end_headers() 
                        self.wfile.write('{"error": "ISBN:ää ei tunnistettu"}'.encode('utf8'))
                    
                    else:
                        book = res['records'][0]
                        name = book['nonPresenterAuthors'][0]['name']
                        names = name.split(',')
                        book_data = {
                            'isbn': isbn,
                            'title': book['title'],
                            'author_last': names[0].strip(),
                            'author_first': names[1].strip(),
                            'year': book['year']
                        }
                        self.send_response(200)
                        self.send_header('content-type', 'application/json') 
                        self.end_headers() 
                        self.wfile.write(json.dumps(book_data).encode('utf8'))

            case _:
                self.send_response(404)
                self.send_header('content-type', 'application/json') 
                self.end_headers() 
                self.wfile.write('{"error": "Ei endpointtia"}'.encode('utf8'))

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