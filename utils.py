import sys
import mysql.connector
from config import server_cnf, db_credentials
from urllib.parse import parse_qs

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