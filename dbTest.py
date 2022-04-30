import mysql.connector

def getConnection():
    try:
        connection = mysql.connector.connect(host="localhost", user="root", passwd="", database="testdb")
        return connection
    except mysql.connector.Error as error:
        print("Failed to insert record {}".format(error))  

# try:
#     connection = getConnection()
#     insert_query = """INSERT INTO test (id) VALUES (123) """
#     cursor = connection.cursor()
#     cursor.execute(insert_query)
#     connection.commit()
#     print(cursor.rowcount, "Record inserted successfully")
#     cursor.close()

# except mysql.connector.Error as error:
#     print("Failed to insert record {}".format(error))

# finally:
#     if connection.is_connected():
#         connection.close()
#         print("MySQL connection is closed")