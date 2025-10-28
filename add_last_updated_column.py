import mysql.connector

# Connect to the database
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='root@12345',
    database='drukride_db'
)

cursor = conn.cursor()

# Add the last_updated column to the Schedule table
alter_query = """
ALTER TABLE Schedule
ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
"""

try:
    cursor.execute(alter_query)
    conn.commit()
    print("Column 'last_updated' added successfully to the Schedule table.")
except mysql.connector.Error as err:
    print(f"Error: {err}")
finally:
    cursor.close()
    conn.close()
