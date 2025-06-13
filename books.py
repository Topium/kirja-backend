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
            res = {'status': '404 NOT FOUND', 'headers': utils.default_headers, 'body': {'message': 'Kirjaa ei löydy'}}
        else:
            book = { k:v for (k,v) in zip([col for col in cur.column_names], rows[0]) }
            res = {'status': '200 OK', 'headers': utils.default_headers, 'body': book}

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
                url = 'https://api.finna.fi/api/v1/search?lookfor={}&type=AllFields&field%5B%5D=title&field%5B%5D=year&field%5B%5D=nonPresenterAuthors&page=1&limit=20'.format(isbn)
                r = requests.get(url)
                res = r.json()
                sys.stderr.write(f'response: {str(res)}\n')

                if res['resultCount'] < 1:
                    sys.stderr.write('no isbn found\n')
                    res = {'status': '404 NOT FOUND', 'headers': utils.default_headers, 'body': {'message': 'ISBN:ää ei tunnistettu'}}
                else:
                    sys.stderr.write('isbn found\n')
                    book = res['records'][0]
                    name = book['nonPresenterAuthors'][0]['name']
                    names = name.split(',')

                    sys.stderr.write('insert book\n')
                    cnx = utils.connect()
                    with cnx.cursor() as cur:
                        query = 'INSERT INTO books (id, isbn, title, author_last, author_first, year) VALUES (NULL, %s, %s, %s, %s, %s)'
                        cur.execute(query, [isbn, book['title'], names[0].strip(), names[1].strip(), int(book['year'])])
                    cnx.commit()
                    res = {'status': '201 CREATED', 'headers': utils.default_headers, 'body': {}}
            cnx.close()

        except Exception as e:
            sys.stderr.write(f'Database error: {str(e)}\n')
            res = {'status': '500 INTERNAL SERVER ERROR', 'headers': utils.default_headers, 'body': {'message': 'Tietokantavirhe'}}

    sys.stderr.write(f'post res: {str(res)}\n')
    return res