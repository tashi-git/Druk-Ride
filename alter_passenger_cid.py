import mysql.connector

# Connect to the database
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='root@12345',
    database='drukride_db'
)

cursor = conn.cursor()

# Alter the passenger_cid column to BIGINT
alter_query = """
ALTER TABLE Booking
MODIFY COLUMN passenger_cid BIGINT
"""

try:
    cursor.execute(alter_query)
    conn.commit()
    print("Column 'passenger_cid' altered to BIGINT successfully.")
except mysql.connector.Error as err:
    print(f"Error: {err}")
finally:
    cursor.close()
    conn.close()
