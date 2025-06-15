import sys, requests, html
import utils

def get_books(params):
    page = int(params['page'][0] if 'page' in params.keys() else 1)
    size = int(params['size'][0] if 'size' in params.keys() else 10)

    try:
        cnx = utils.connect()
        with cnx.cursor() as cur:
            cur.execute('SELECT COUNT(*) AS row_count FROM books;')
            row_count = cur.fetchone()[0]
        query = 'SELECT * FROM books WHERE id >= %s LIMIT %s;'
        with cnx.cursor() as cur:
            cur.execute(query, [(page - 1) * size, size])
            rows = cur.fetchall()
        book = [{ k:v for (k,v) in zip([col for col in cur.column_names], row) } for row in rows]
        data = { 'page': page, 'size': size, 'total': row_count, 'data': book}
        res = {'status': '200 OK', 'headers': utils.default_headers + utils.htmx_headers, 'body': data}

    except Exception as e:
        sys.stderr.write(f'Database error: {str(e)}\n')
        res = {'status': '500 INTERNAL SERVER ERROR', 'headers': utils.default_headers + utils.htmx_headers, 'body': {'message': 'Tietokantavirhe'}}
        
    cnx.close()
    return res

def get_book(params):
    isbn = int(params['isbn'][0] if 'isbn' in params.keys() else 0)
    query = 'SELECT * FROM books WHERE isbn = %s'
    try:
        cnx = utils.connect()
        with cnx.cursor() as cur:
            cur.execute(query, [isbn])
            rows = cur.fetchall()
        if len(rows) == 0:
            book = fetch_book_info(isbn)
            if (len(book) > 0):
                res = {'status': '200 OK', 'headers': utils.default_headers, 'body': {**book, 'source': 'Finna'}}
            else:
                res = {'status': '404 NOT FOUND', 'headers': utils.default_headers, 'body': {'message': 'Kirjaa ei löydy'}}
        else:
            book = { k:v for (k,v) in zip([col for col in cur.column_names], rows[0]) }
            res = {'status': '200 OK', 'headers': utils.default_headers, 'body': {**book, 'source': 'topsu'}}

    except Exception as e:
        sys.stderr(f'Database error: {str(e)}\n')
        res = {'status': '500 INTERNAL SERVER ERROR', 'headers': utils.default_headers, 'body': {'message': 'Tietokantavirhe'}}

    cnx.close()
    return res

def post_book(data):
    sys.stderr.write('start db post\n')
    if not 'isbn' in data.keys():
        sys.stderr.write('no isbn\n')
        res = {'status': '404 NOT FOUND', 'headers': utils.default_headers, 'body': {'message': 'ISBN-parametri puuttuu!'}}
    elif not utils.verify_isbn(html.escape(data.get('isbn', '')[0])):
        sys.stderr.write('not isbn\n')
        res = {'status': '404 NOT FOUND', 'headers': utils.default_headers, 'body': {'message': 'ISBN ei kelpaa'}}
    else:
        try:
            isbn = html.escape(data.get('isbn', '')[0])
            cnx = utils.connect()
            with cnx.cursor() as cur:
                query = 'SELECT * FROM books WHERE isbn = %s;'
                cur.execute(query, [isbn])
                rows = cur.fetchall()
            if len(rows) > 0:
                sys.stderr.write('isbn exists\n')
                res = {'status': '409 CONFLICT', 'headers': utils.default_headers, 'body': {'message': 'ISBN on jo kirjattu'}}
            else:
                sys.stderr.write('request isbn\n')
                book = fetch_book_info(isbn)
                if len(book) < 1:
                    res = {'status': '404 NOT FOUND', 'headers': utils.default_headers, 'body': {'message': 'ISBN:ää ei tunnistettu'}}
                else:
                    sys.stderr.write('isbn found\n')
                    sys.stderr.write('insert book\n')
                    cnx = utils.connect()
                    with cnx.cursor() as cur:
                        query = 'INSERT INTO books (id, isbn, title, author_last, author_first, year) VALUES (NULL, %s, %s, %s, %s, %s)'
                        cur.execute(query, [book['isbn'], book['title'], book['author_last'], book['author_first'], book['year']])
                    cnx.commit()
                    res = {'status': '201 CREATED', 'headers': utils.default_headers, 'body': {}}
            cnx.close()

        except Exception as e:
            sys.stderr.write(f'Database error: {str(e)}\n')
            res = {'status': '500 INTERNAL SERVER ERROR', 'headers': utils.default_headers, 'body': {'message': 'Tietokantavirhe'}}

    sys.stderr.write(f'post res: {str(res)}\n')
    return res

def fetch_book_info(isbn):
    isbn = str(isbn)
    sys.stderr.write('request isbn\n')
    url = 'https://api.finna.fi/api/v1/search?lookfor={}&type=AllFields&field%5B%5D=title&field%5B%5D=year&field%5B%5D=nonPresenterAuthors&page=1&limit=20'.format(isbn)
    r = requests.get(url)
    data = r.json()
    sys.stderr.write(f'Response from Finna: {str(data)}\n')
    book = {}

    if data['resultCount'] < 1 or data['status'] != 'OK':
        sys.stderr.write('no isbn found\n')
    else:
        sys.stderr.write('isbn found\n')
        record = data['records'][0]
        name = record['nonPresenterAuthors'][0]['name']
        book['isbn'] = isbn
        book['title'] = record['title']
        book['author_first'] = name[1:].strip()
        book['author_last'] = name[0].strip()
        book['year'] = int(record['year'])
    return book