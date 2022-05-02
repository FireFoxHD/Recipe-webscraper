import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')

def getConnection():
    try:
        connection = mysql.connector.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, database=DB_NAME)
        return connection
    except mysql.connector.Error as error:
        print("Failed to insert record {}".format(error))

  

