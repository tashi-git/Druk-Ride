import pytest
from app import app as flask_app, create_connection
from flask import session

# -----------------------------
# Test client fixture
# -----------------------------
@pytest.fixture
def client():
    """Create a Flask test client for sending HTTP requests to the app."""
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test_secret_key'
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client

# -----------------------------
# Database connection fixture
# -----------------------------
@pytest.fixture(scope='function')
def db_connection():
    """
    Provide a real database connection for tests.
    Rolls back changes after each test to keep the DB clean.
    """
    conn = create_connection()  # call without db_name
    cursor = conn.cursor(dictionary=True)  # rows as dicts for easy JSON serialization
    yield conn, cursor
    conn.rollback()  # undo changes after each test
    cursor.close()
    conn.close()

# -----------------------------
# Helper functions
# -----------------------------
def insert_test_user(cursor, conn, phone='9998887777', name='Test User'):
    """Insert a test user and return user ID."""
    cursor.execute("""
        INSERT INTO users (name, phone, email, password, user_type)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE name=%s
    """, (name, phone, f'{phone}@example.com', 'password123', 'customer', name))
    conn.commit()
    cursor.execute("SELECT id FROM users WHERE phone=%s", (phone,))
    return cursor.fetchone()['id']

def insert_test_schedule(cursor, conn, bus_no='TEST001', ticket_price=500):
    """Insert a test bus schedule and return schedule ID."""
    cursor.execute("""
        INSERT INTO Schedule (bus_no, route_id, reporting_time, travel_time, available_seats, ticket_price)
        VALUES (%s, 1, '08:00:00', '12:00:00', 40, %s)
    """, (bus_no, ticket_price))
    conn.commit()
    cursor.execute("SELECT id FROM Schedule WHERE bus_no=%s", (bus_no,))
    return cursor.fetchone()['id']

# -----------------------------
# Test Cases
# -----------------------------
def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'DrukRide' in response.data

def test_user_registration(client, db_connection):
    conn, cursor = db_connection
    response = client.post('/register', data={
        'name': 'New User',
        'phone': '8887776666',
        'email': 'newuser@example.com',
        'password': 'password123',
        'user_type': 'customer'
    })
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

    cursor.execute("SELECT * FROM users WHERE phone='8887776666'")
    user = cursor.fetchone()
    assert user['name'] == 'New User'

def test_user_login(client, db_connection):
    conn, cursor = db_connection
    user_id = insert_test_user(cursor, conn, phone='1112223333', name='Login User')

    response = client.post('/login', data={
        'username': '1112223333',
        'password': 'password123'
    })
    assert response.status_code == 302
    assert '/' in response.headers['Location']

def test_booking_search(client, db_connection):
    conn, cursor = db_connection
    schedule_id = insert_test_schedule(cursor, conn, bus_no='BOOK001', ticket_price=500)

    response = client.post('/book', data={
        'from': 'Thimphu',
        'to': 'Phuentsholing',
        'date': '2025-01-01'
    })
    assert response.status_code == 200
    assert b'Available Buses' in response.data

def test_seat_booking(client, db_connection):
    conn, cursor = db_connection
    user_id = insert_test_user(cursor, conn)
    schedule_id = insert_test_schedule(cursor, conn, bus_no='SEAT001')

    with client.session_transaction() as sess:
        sess['user_id'] = user_id

    response = client.post('/booking', data={'bus_no': 'SEAT001'})
    assert response.status_code == 200
    assert b'Select Your Seats' in response.data

def test_counter_dashboard(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_type'] = 'counter'

    response = client.get('/counter_dashboard')
    assert response.status_code == 200
    assert b'Counter Dashboard' in response.data

def test_booking_cancellation(client, db_connection):
    conn, cursor = db_connection
    user_id = insert_test_user(cursor, conn)
    schedule_id = insert_test_schedule(cursor, conn)
    cursor.execute("INSERT INTO Booking (user_id, schedule_id, status) VALUES (%s, %s, 'Confirmed')",
                   (user_id, schedule_id))
    conn.commit()
    cursor.execute("SELECT id FROM Booking WHERE user_id=%s AND schedule_id=%s", (user_id, schedule_id))
    booking_id = cursor.fetchone()['id']

    with client.session_transaction() as sess:
        sess['user_id'] = user_id
        sess['user_type'] = 'counter'

    response = client.get(f'/cancel_booking/{booking_id}')
    assert response.status_code == 302
    assert '/counter_dashboard' in response.headers['Location']

def test_schedule_update(client, db_connection):
    conn, cursor = db_connection
    schedule_id = insert_test_schedule(cursor, conn, bus_no='UPD001')

    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_type'] = 'counter'

    response = client.post('/update_schedule', data={
        'schedule_id': schedule_id,
        'departure_time': '09:00:00',
        'arrival_time': '13:00:00'
    })
    assert response.status_code == 302
    assert '/counter_dashboard' in response.headers['Location']

def test_my_bookings(client, db_connection):
    conn, cursor = db_connection
    user_id = insert_test_user(cursor, conn)
    schedule_id = insert_test_schedule(cursor, conn)
    cursor.execute("INSERT INTO Booking (user_id, schedule_id, status) VALUES (%s, %s, 'Confirmed')",
                   (user_id, schedule_id))
    conn.commit()

    with client.session_transaction() as sess:
        sess['user_id'] = user_id

    response = client.get('/my_bookings')
    assert response.status_code == 200
    assert b'My Bookings' in response.data

def test_logout(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'Test User'

    response = client.get('/logout')
    assert response.status_code == 302
    assert '/' in response.headers['Location']

    with client.session_transaction() as sess:
        assert 'user_id' not in sess

if __name__ == '__main__':
    pytest.main([__file__])
