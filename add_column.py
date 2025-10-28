import mysql.connector

# Connect to the database
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='root@12345',
    database='drukride_db'
)

cursor = conn.cursor()

# Add the user_type column to the Booking table
alter_query = """
ALTER TABLE Booking
ADD COLUMN user_type VARCHAR(20) NOT NULL DEFAULT 'user'
"""

try:
    cursor.execute(alter_query)
    conn.commit()
    print("Column 'user_type' added successfully to the Booking table.")
except mysql.connector.Error as err:
    print(f"Error: {err}")
finally:
    cursor.close()
    conn.close()
