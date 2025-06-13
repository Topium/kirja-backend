import sys, json
from urllib.parse import parse_qs
import utils
import books

routes = {
    ('GET', '/books/'): books.get_books,
    ('GET', '/book/'): books.get_book,
    ('POST', '/book/'): books.post_book,
}

def handle_options():
    return {'status': '200 OK', 'headers': utils.default_headers + utils.htmx_headers, 'body': {}}
    
def app(environ, start_fn):
    # for (k,v) in environ.items():
    #     sys.stdout.write(f'{k}: {v}\n')
    path_list = environ['REQUEST_URI'].split('/')
    sys.stderr.write(f'path {str(path_list)}\n')

    if environ['REQUEST_METHOD'] == 'OPTIONS':
        res = handle_options()
        start_fn(res['status'], res['headers'])
        return [json.dumps(res['body']).encode()]

    elif environ['REQUEST_METHOD'] == 'GET':
        handler = routes.get((environ['REQUEST_METHOD'], environ['PATH_INFO']))
        if handler:
            params = parse_qs(environ['QUERY_STRING'])
            res = handler(params)
        else:
            res = {'status': '404 NOT FOUND', 'headers': utils.default_headers, 'body': {'message': 'Polku ei kelpaa (puuttuuko lopusta kauttaviiva?)'}}

        start_fn(res['status'], res['headers'])
        return [json.dumps(res['body']).encode()]
    
    elif environ['REQUEST_METHOD'] == 'POST':
        sys.stderr.write('\nstart post\n')
        
        handler = routes.get((environ['REQUEST_METHOD'], environ['PATH_INFO']))
        if handler:
            data = utils.get_post_params(environ)
            res = handler(data)
        else:
            res = {'status': '404 NOT FOUND', 'headers': utils.default_headers, 'body': {'message': 'Polku ei kelpaa (puuttuuko lopusta kauttaviiva?)'}}

        start_fn(res['status'], res['headers'])
        return [json.dumps(res['body']).encode()]
    
    elif environ['REQUEST_METHOD'] == 'DELETE':
        start_fn('405 METHOD NOT ALLOWED', utils.default_headers + utils.htmx_headers)
        return [json.dumps({'message': 'un erreur'}).encode()]
        
    else:
        body= b''  # b'' for consistency on Python 3.0
        try:
            length= int(environ.get('CONTENT_LENGTH', '0'))
        except ValueError:
            length= 0
        if length!=0:
            body= environ['wsgi.input'].read(length)
        start_fn('200 OK', [('Content-Type', 'text/plain')])
        return [str(environ), str(body).encode()]