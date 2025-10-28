import mysql.connector

# Connect to the database
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='root@12345',
    database='drukride_db'
)

cursor = conn.cursor()

# First, update any out-of-range values to fit within INT range
update_query = """
UPDATE Booking
SET passenger_cid = FLOOR(RAND() * 100000000) + 100000000
WHERE passenger_cid > 2147483647
"""

try:
    cursor.execute(update_query)
    conn.commit()
    print("Updated out-of-range passenger_cid values.")

    # Now alter the column back to INT
    alter_query = """
    ALTER TABLE Booking
    MODIFY COLUMN passenger_cid INT
    """
    cursor.execute(alter_query)
    conn.commit()
    print("Column 'passenger_cid' rolled back to INT successfully.")
except mysql.connector.Error as err:
    print(f"Error: {err}")
finally:
    cursor.close()
    conn.close()
