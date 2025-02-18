import sys, cgi, requests, json
import mysql.connector
from config import server_cnf, db_credentials
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

cors_origin=server_cnf['cors-origin']

def connect():
    try:
        cnx = mysql.connector.connect(
            user=db_credentials['user'],
            password=db_credentials['password'],
            database=db_credentials['database'],
            host=db_credentials['host']
            )
    except mysql.connector.Error as err:
        print(err)
        return None
    else:
        return cnx
    
def verify_isbn(isbn):
    sys.stderr.write(f'isbn: {isbn}')
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
    def do_OPTIONS(self):
        print('options', self)
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', cors_origin) 
        self.send_header('Access-Control-Allow-Headers', 'hx-current-url') 
        self.send_header('Access-Control-Allow-Headers', 'hx-request') 
        self.send_header('Access-Control-Allow-Headers', 'hx-target') 
        self.end_headers() 
        self.wfile.write(b'Home')
    def do_GET(self):
        print(self.path)
        full_path = urlparse(self.path).path.split('/')
        print(full_path)
        print(urlparse(self.path))
        
        if urlparse(self.path).path == '/favicon.ico':
            with open('book-32.png', 'rb') as f:
                self.send_response(200)
                self.send_header('content-type', 'image/png') 
                self.end_headers() 
                self.wfile.write(f.read())

        else:
            self.send_response(404)
            self.send_header('content-type', 'application/json') 
            self.end_headers() 
            self.wfile.write('{"error": "Ei endpointtia"}'.encode('utf8'))

    def do_POST(self):
        path = urlparse(self.path).path
        if path == '/books':
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST',
                        'CONTENT_TYPE': self.headers['Content-Type'],
                        }
            )
            try:
                isbn = form.getvalue('isbn').strip()
            except:
                self.send_response(400)
                self.send_header('content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', cors_origin)   
                self.send_header('Access-Control-Allow-Headers', 'hx-target') 
                self.end_headers() 
                self.wfile.write('{"error": "Parametri ei validi"}'.encode('utf8'))

            cnx = connect()
            with cnx.cursor() as cur:
                query = 'SELECT * FROM books WHERE isbn = %s;'
                cur.execute(query, [isbn])
                rows = cur.fetchall()
            cnx.close()

            if len(rows) > 0:
                self.send_response(200)
                self.send_header('content-type', 'application/json') 
                self.send_header('Access-Control-Allow-Origin', cors_origin)  
                self.end_headers() 
                self.wfile.write('{"msg": "ISBN jo käytössä"}'.encode('utf8'))

            elif not verify_isbn(isbn):
                self.send_response(400)
                self.send_header('content-type', 'application/json') 
                self.send_header('Access-Control-Allow-Origin', cors_origin)  
                self.send_header('Access-Control-Allow-Headers', 'hx-target') 
                self.end_headers() 
                self.wfile.write('{"error": "ISBN ei validi"}'.encode('utf8'))

            else:
                print('isbn', isbn)
                url = 'https://api.finna.fi/api/v1/search?lookfor={}&type=AllFields&field%5B%5D=title&field%5B%5D=year&field%5B%5D=nonPresenterAuthors&page=1&limit=20'.format(isbn)
                r = requests.get(url)
                res = r.json()
                print('res', res)
                
                if res['resultCount'] < 1:
                    self.send_response(400)
                    self.send_header('content-type', 'application/json') 
                    self.send_header('Access-Control-Allow-Origin', cors_origin)  
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

                    cnx = connect()
                    with cnx.cursor() as cur:
                        query = 'INSERT INTO books (id, isbn, title, author_last, author_first, year) VALUES (NULL, %s, %s, %s, %s, %s)'
                        cur.execute(query, [isbn, book['title'], names[0].strip(), names[1].strip(), int(book['year'])])
                    cnx.commit()
                    cnx.close()

                    self.send_response(201)
                    self.send_header('content-type', 'application/json') 
                    self.send_header('Access-Control-Allow-Origin', cors_origin)  
                    self.end_headers() 
                    self.wfile.write(json.dumps(book_data).encode('utf8'))

        else:
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

if __name__ == '__main__':
    runserver()

def get_books(query, default_headers):
    res = {'status': '500', 'headers': default_headers, 'body': {'message': 'Tuntematon virhe'}}
    params = parse_qs(query)
    page = int(params['page'][0] if 'page' in params.keys() else 1)
    size = int(params['size'][0] if 'size' in params.keys() else 10)

    try:
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
        book = [{ k:v for (k,v) in zip([col for col in cur.column_names], row) } for row in rows]
        data = { 'page': page, 'size': size, 'total': row_count, 'data': book}
        res = {'status': '200 OK', 'headers': default_headers, 'body': data}
    except Exception as e:
        res = {'status': '500 OK', 'headers': default_headers, 'body': {'message': str(e)}}
    return res

def get_book(isbn, default_headers):
    query = 'SELECT * FROM books WHERE isbn = %s'
    cnx = connect()
    with cnx.cursor() as cur:
        cur.execute(query, [isbn])
        rows = cur.fetchall()
        print(rows)
    if len(rows) == 0:
        res = {'status': '404 NOT FOUND', 'headers': default_headers, 'body': {'message': 'Kirjaa ei löydy'}}
    else:
        book = { k:v for (k,v) in zip([col for col in cur.column_names], rows[0]) }
        res = {'status': '200 OK', 'headers': default_headers, 'body': book}
    return res
    
def app(environ, start_fn):
    default_headers = [('Content-Type', 'application/json'),('Access-Control-Allow-Origin', cors_origin)]
    if environ['REQUEST_METHOD'] == 'GET':
        res = {'status': '404 NOT FOUND', 'headers': default_headers, 'body': {'message': 'Polku ei kelpaa (muista päättävä kauttaviiva!)'}}
        path_list = environ['SCRIPT_URL'].split('/')
        sys.stderr.write(f'path {str(path_list)}')
        if len(path_list) == 3 and path_list[1] == 'books' and path_list[2] == '':
            res = get_books(environ['QUERY_STRING'], default_headers)
        elif len(path_list) == 4 and path_list[1] == 'books' and verify_isbn(path_list[2]):
            res = get_book(path_list[2], default_headers)

        start_fn(res['status'], res['headers'])
        return [json.dumps(res['body'])]
    
    elif environ['REQUEST_METHOD'] == 'POST':
        diipa = ''
        daapa = ''
        try:
            length= int(environ.get('CONTENT_LENGTH', '0'))
        except ValueError:
            length= 0
        if length!=0:
            body= environ['wsgi.input'].read(length)
            d = parse_qs(body.decode())
            diipa = d.get('diipa', '')[0]
            daapa = d.get('daapa', '')[0]

        start_fn('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps({'body': {'diipa': diipa, 'daapa': daapa}})]
    
    else:
        body= b''  # b'' for consistency on Python 3.0
        try:
            length= int(environ.get('CONTENT_LENGTH', '0'))
        except ValueError:
            length= 0
        if length!=0:
            body= environ['wsgi.input'].read(length)
        start_fn('200 OK', [('Content-Type', 'text/plain')])
        return [str(environ), str(body)]