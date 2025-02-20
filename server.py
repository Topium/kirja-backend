import sys, cgi, requests, json, html
import mysql.connector
from config import server_cnf, db_credentials
from urllib.parse import urlparse, parse_qs

cors_origin=server_cnf['cors-origin']
default_headers = [
    ('Content-Type', 'application/json'),
    ('Access-Control-Allow-Origin', cors_origin)
]
htmx_headers = [
    ('Access-Control-Allow-Headers', 'hx-current-url'),
    ('Access-Control-Allow-Headers', 'hx-request'),
    ('Access-Control-Allow-Headers', 'hx-target')
]

def connect():
    try:
        cnx = mysql.connector.connect(
            user=db_credentials['user'],
            password=db_credentials['password'],
            database=db_credentials['database'],
            host=db_credentials['host']
        )
    except mysql.connector.Error as err:
        sys.stderr.write(f'Connection failure: {str(err)}\n')
        return None
    else:
        return cnx
    
def verify_isbn(isbn):
    sys.stderr.write(f'verify isbn: {isbn}\n')
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
    
def get_post_params(environ):
    try:
        length = int(environ.get('CONTENT_LENGTH', '0'))
    except ValueError:
        sys.stderr.write('params error ')
        length = 0
        
    if length != 0:
        sys.stderr.write('got params\n')
        body = environ['wsgi.input'].read(length)
        return parse_qs(body.decode())
    else:
        return {}

def handle_options():
    return {'status': '200 OK', 'headers': default_headers + htmx_headers, 'body': {}}

def get_books(query):
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
        book = [{ k:v for (k,v) in zip([col for col in cur.column_names], row) } for row in rows]
        data = { 'page': page, 'size': size, 'total': row_count, 'data': book}
        res = {'status': '200 OK', 'headers': default_headers + htmx_headers, 'body': data}
    except Exception as e:
        sys.stderr.write(f'Database error: {str(e)}\n')
        res = {'status': '500 INTERNAL SERVER ERROR', 'headers': default_headers + htmx_headers, 'body': {'message': 'Tietokantavirhe'}}
    cnx.close()
    return res

def get_book(isbn):
    query = 'SELECT * FROM books WHERE isbn = %s'
    try:
        cnx = connect()
        with cnx.cursor() as cur:
            cur.execute(query, [isbn])
            rows = cur.fetchall()
        if len(rows) == 0:
            res = {'status': '404 NOT FOUND', 'headers': default_headers, 'body': {'message': 'Kirjaa ei löydy'}}
        else:
            book = { k:v for (k,v) in zip([col for col in cur.column_names], rows[0]) }
            res = {'status': '200 OK', 'headers': default_headers, 'body': book}
    except Exception as e:
        sys.stderr(f'Database error: {str(e)}\n')
        res = {'status': '500 INTERNAL SERVER ERROR', 'headers': default_headers, 'body': {'message': 'Tietokantavirhe'}}
    cnx.close()
    return res

def post_book(isbn):
    sys.stderr.write('start db post\n')
    try:
        cnx = connect()
        with cnx.cursor() as cur:
            query = 'SELECT * FROM books WHERE isbn = %s;'
            cur.execute(query, [isbn])
            rows = cur.fetchall()
        if len(rows) > 0:
            sys.stderr.write('isbn exists\n')
            res = {'status': '409 CONFLICT', 'headers': default_headers, 'body': {'message': 'ISBN on jo kirjattu'}}
        else:
            sys.stderr.write('request isbn\n')
            url = 'https://api.finna.fi/api/v1/search?lookfor={}&type=AllFields&field%5B%5D=title&field%5B%5D=year&field%5B%5D=nonPresenterAuthors&page=1&limit=20'.format(isbn)
            r = requests.get(url)
            res = r.json()
            sys.stderr.write(f'response: {str(res)}\n')

            if res['resultCount'] < 1:
                sys.stderr.write('no isbn found\n')
                res = {'status': '404 NOT FOUND', 'headers': default_headers, 'body': {'message': 'ISBN:ää ei tunnistettu'}}
            else:
                sys.stderr.write('isbn found\n')
                book = res['records'][0]
                name = book['nonPresenterAuthors'][0]['name']
                names = name.split(',')

                sys.stderr.write('insert book\n')
                cnx = connect()
                with cnx.cursor() as cur:
                    query = 'INSERT INTO books (id, isbn, title, author_last, author_first, year) VALUES (NULL, %s, %s, %s, %s, %s)'
                    cur.execute(query, [isbn, book['title'], names[0].strip(), names[1].strip(), int(book['year'])])
                cnx.commit()
                res = {'status': '201 CREATED', 'headers': default_headers, 'body': {}}

    except Exception as e:
        sys.stderr.write(f'Database error: {str(e)}\n')
        res = {'status': '500 INTERNAL SERVER ERROR', 'headers': default_headers, 'body': {'message': 'Tietokantavirhe'}}
    cnx.close()
    sys.stderr.write(f'post res: {str(res)}\n')
    return res
    
def app(environ, start_fn):

    path_list = environ['SCRIPT_URL'].split('/')
    sys.stderr.write(f'path {str(path_list)}')

    if environ['REQUEST_METHOD'] == 'OPTIONS':
        res = handle_options()
        start_fn(res['status'], res['headers'])
        return [json.dumps(res['body'])]

    elif environ['REQUEST_METHOD'] == 'GET':
        if len(path_list) == 3 and path_list[1] == 'books-api' and path_list[2] == '':
            res = get_books(environ['QUERY_STRING'])
        elif len(path_list) == 4 and path_list[1] == 'books-api' and verify_isbn(path_list[2]):
            res = get_book(path_list[2])
        else:
            res = {'status': '404 NOT FOUND', 'headers': default_headers, 'body': {'message': 'Polku ei kelpaa (puuttuuko lopusta kauttaviiva?)'}}

        start_fn(res['status'], res['headers'])
        return [json.dumps(res['body'])]
    
    elif environ['REQUEST_METHOD'] == 'POST':
        sys.stderr.write('\nstart post\n')
        d = get_post_params(environ)
        if not 'isbn' in d.keys():
            sys.stderr.write('no isbn\n')
            res = {'status': '404 NOT FOUND', 'headers': default_headers, 'body': {'message': 'ISBN-parametri puuttuu!'}}
        elif len(path_list) != 3 or path_list[1] != 'books-api' or path_list[2] != '':
            sys.stderr.write('bad path\n')
            res = {'status': '404 NOT FOUND', 'headers': default_headers, 'body': {'message': 'Polku ei kelpaa (puuttuuko lopusta kauttaviiva?)'}}
        else:
            sys.stderr.write(f'gonna post {str(d)}\n')
            isbn = d.get('isbn', '')[0]
            isbn = html.escape(isbn)
            if verify_isbn(isbn):
                res = post_book(isbn)
            else:
                sys.stderr.write('not isbn\n')
                res = {'status': '404 NOT FOUND', 'headers': default_headers, 'body': {'message': 'ISBN ei kelpaa'}}

        start_fn(res['status'], res['headers'])
        return [json.dumps(res['body'])]
    
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