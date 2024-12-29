import mysql.connector
from config import db_credentials

try:
  cnx = mysql.connector.connect(
    user=db_credentials['user'],
    password=db_credentials['password'],
    database=db_credentials['database']
    )
except mysql.connector.Error as err:
    print(err)
else:
  cnx.close()