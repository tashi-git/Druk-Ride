import mysql.connector
from mysql.connector import Error

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',  
            user='root',       
            password='root@12345',       
            database='drukride_db'  
        )
        if connection.is_connected():
            print("Connected to MySQL database")
            
    except Error as e:
        print(f"Error: '{e}'")
    return connection

def close_connection(connection):
    """Close the database connection."""
    if connection and connection.is_connected():
        connection.close()
        print("Connection closed")
