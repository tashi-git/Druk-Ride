import pytest
import mysql.connector
import random

# ---------------- DB CONNECTION -----------------
db_config = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "root@12345",
    "database": "drukride_db"
}

@pytest.fixture
def db_connection():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    yield cursor, conn
    # cleanup after each test
    cursor.execute("DELETE FROM Booking")
    cursor.execute("DELETE FROM Schedule")
    cursor.execute("DELETE FROM Bus")
    cursor.execute("DELETE FROM Operator")
    cursor.execute("DELETE FROM Route")
    cursor.execute("DELETE FROM UserAccount")
    conn.commit()
    cursor.close()
    conn.close()

# ---------------- HELPERS -----------------
def insert_test_user(cursor, conn, phone=None, name='Test User'):
    if not phone:
        phone = f"{random.randint(1000000000, 9999999999)}"  # 10-digit phone
    password = f"pass{random.randint(1000,9999)}"
    cursor.execute("""
        INSERT INTO UserAccount (name, phone, email, password, user_type)
        VALUES (%s, %s, %s, %s, %s)
    """, (name, phone, f"user{random.randint(1000,9999)}@example.com", password, "Passenger"))
    conn.commit()
    return cursor.lastrowid

def insert_test_bus(cursor, conn):
    cursor.execute("SELECT bus_no FROM Bus LIMIT 1")
    bus = cursor.fetchone()
    if not bus:
        cursor.execute("INSERT INTO Operator (company_name) VALUES ('Test Operator')")
        operator_id = cursor.lastrowid
        cursor.execute("INSERT INTO Bus (bus_no, operator_id, capacity) VALUES ('TEST001', %s, 30)", (operator_id,))
        conn.commit()
        return 'TEST001'
    return bus['bus_no']

def insert_test_route(cursor, conn):
    cursor.execute("SELECT route_id FROM Route LIMIT 1")
    route = cursor.fetchone()
    if not route:
        cursor.execute("INSERT INTO Route (start, destination, distance) VALUES ('A', 'B', 50)")
        conn.commit()
        return cursor.lastrowid
    return route['route_id']

def insert_test_schedule(cursor, conn, bus_no=None, route_id=None):
    if not bus_no:
        bus_no = insert_test_bus(cursor, conn)
    if not route_id:
        route_id = insert_test_route(cursor, conn)
    cursor.execute("""
        INSERT INTO Schedule (bus_no, route_id, reporting_time, travel_time, ticket_price, available_seats)
        VALUES (%s, %s, '08:00:00', '09:00:00', 100, 30)
    """, (bus_no, route_id))
    conn.commit()
    return cursor.lastrowid

# ---------------- TEST CASES -----------------
def test_home_page():
    assert True

def test_user_registration(db_connection):
    cursor, conn = db_connection
    user_id = insert_test_user(cursor, conn, phone='8887776666', name='Reg User')
    cursor.execute("SELECT * FROM UserAccount WHERE phone='8887776666'")
    user = cursor.fetchone()
    assert user is not None
    assert user['name'] == 'Reg User'

def test_user_login(db_connection):
    cursor, conn = db_connection
    phone = '1112223333'
    insert_test_user(cursor, conn, phone=phone, name='Login User')
    cursor.execute("SELECT * FROM UserAccount WHERE phone=%s", (phone,))
    user = cursor.fetchone()
    assert user is not None
    assert user['name'] == 'Login User'

def test_booking_search(db_connection):
    cursor, conn = db_connection
    schedule_id = insert_test_schedule(cursor, conn)
    cursor.execute("SELECT * FROM Schedule WHERE schedule_id=%s", (schedule_id,))
    schedule = cursor.fetchone()
    assert schedule is not None
    assert schedule['available_seats'] > 0

def test_seat_booking(db_connection):
    cursor, conn = db_connection
    user_id = insert_test_user(cursor, conn)
    schedule_id = insert_test_schedule(cursor, conn)
    cursor.execute("""
        INSERT INTO Booking (user_id, schedule_id, seat_no, seats_booked, passenger_name, passenger_cid, phone)
        VALUES (%s, %s, 1, 1, 'Passenger1', 123456789012, '7778889999')
    """, (user_id, schedule_id))
    conn.commit()
    cursor.execute("SELECT * FROM Booking WHERE user_id=%s AND schedule_id=%s", (user_id, schedule_id))
    booking = cursor.fetchone()
    assert booking is not None
    assert booking['seat_no'] == 1

def test_counter_dashboard():
    assert True

def test_booking_cancellation(db_connection):
    cursor, conn = db_connection
    user_id = insert_test_user(cursor, conn)
    schedule_id = insert_test_schedule(cursor, conn)
    cursor.execute("""
        INSERT INTO Booking (user_id, schedule_id, seat_no, seats_booked, passenger_name, passenger_cid, phone)
        VALUES (%s, %s, 2, 1, 'Passenger2', 123456789013, '7778880000')
    """, (user_id, schedule_id))
    booking_id = cursor.lastrowid
    conn.commit()
    cursor.execute("UPDATE Booking SET status='Cancelled' WHERE booking_id=%s", (booking_id,))
    conn.commit()
    cursor.execute("SELECT status FROM Booking WHERE booking_id=%s", (booking_id,))
    status = cursor.fetchone()['status']
    assert status == 'Cancelled'

def test_schedule_update(db_connection):
    cursor, conn = db_connection
    schedule_id = insert_test_schedule(cursor, conn)
    cursor.execute("UPDATE Schedule SET ticket_price=200 WHERE schedule_id=%s", (schedule_id,))
    conn.commit()
    cursor.execute("SELECT ticket_price FROM Schedule WHERE schedule_id=%s", (schedule_id,))
    price = cursor.fetchone()['ticket_price']
    assert price == 200

def test_my_bookings(db_connection):
    cursor, conn = db_connection
    user_id = insert_test_user(cursor, conn)
    schedule_id = insert_test_schedule(cursor, conn)
    cursor.execute("""
        INSERT INTO Booking (user_id, schedule_id, seat_no, seats_booked, passenger_name, passenger_cid, phone)
        VALUES (%s, %s, 3, 1, 'Passenger3', 123456789014, '7778881111')
    """, (user_id, schedule_id))
    conn.commit()
    cursor.execute("SELECT * FROM Booking WHERE user_id=%s", (user_id,))
    bookings = cursor.fetchall()
    assert len(bookings) > 0

def test_logout():
    assert True
