import pytest
from app import app as flask_app, create_connection
from flask import session

# -----------------------------
# Test client fixture
# -----------------------------
@pytest.fixture
def client():
    """
    Create a Flask test client for sending HTTP requests
    to the app in a test environment.
    """
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test_secret_key'
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client  # provide the test client to the tests

# -----------------------------
# Database connection fixture
# -----------------------------
@pytest.fixture(scope='function')
def db_connection():
    """
    Provide a real database connection for testing.
    Uses a separate test database to avoid polluting production data.
    Rolls back changes after each test to keep DB clean.
    """
    conn = create_connection(db_name="drukride_test_db")  # Connect to test DB
    cursor = conn.cursor(dictionary=True)  # Return rows as dictionaries (JSON-serializable)
    yield conn, cursor
    conn.rollback()  # undo any changes made by the test
    cursor.close()
    conn.close()

# -----------------------------
# Helper functions
# -----------------------------
def insert_test_user(cursor, conn, phone='9998887777', name='Test User'):
    """
    Insert a test user into the users table.
    Returns the user ID for further test use.
    """
    cursor.execute("""
        INSERT INTO users (name, phone, email, password, user_type)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE name=%s
    """, (name, phone, f'{phone}@example.com', 'password123', 'customer', name))
    conn.commit()
    cursor.execute("SELECT id FROM users WHERE phone=%s", (phone,))
    return cursor.fetchone()['id']

def insert_test_schedule(cursor, conn, bus_no='TEST001', ticket_price=500):
    """
    Insert a test bus schedule.
    Returns the schedule ID for booking-related tests.
    """
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
    """Test that the home page loads successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'DrukRide' in response.data

def test_user_registration(client, db_connection):
    """
    Test user registration:
    1. Submit a registration form.
    2. Check redirect to login page.
    3. Verify user is actually inserted into the DB.
    """
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

    # Check that user exists in the DB
    cursor.execute("SELECT * FROM users WHERE phone='8887776666'")
    user = cursor.fetchone()
    assert user['name'] == 'New User'

def test_user_login(client, db_connection):
    """
    Test user login:
    1. Insert a test user.
    2. Submit login form.
    3. Check redirect to home page.
    """
    conn, cursor = db_connection
    user_id = insert_test_user(cursor, conn, phone='1112223333', name='Login User')

    response = client.post('/login', data={
        'username': '1112223333',
        'password': 'password123'
    })
    assert response.status_code == 302
    assert '/' in response.headers['Location']

def test_booking_search(client, db_connection):
    """
    Test searching for available buses:
    1. Insert a test schedule.
    2. Submit booking search form.
    3. Verify search results appear.
    """
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
    """
    Test seat selection and booking:
    1. Insert a schedule.
    2. Set a user in session.
    3. Post booking request.
    4. Check seat selection page is returned.
    """
    conn, cursor = db_connection
    user_id = insert_test_user(cursor, conn)
    schedule_id = insert_test_schedule(cursor, conn, bus_no='SEAT001')

    with client.session_transaction() as sess:
        sess['user_id'] = user_id

    response = client.post('/booking', data={'bus_no': 'SEAT001'})
    assert response.status_code == 200
    assert b'Select Your Seats' in response.data

def test_counter_dashboard(client):
    """Test that the counter dashboard page is accessible to counter users."""
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_type'] = 'counter'

    response = client.get('/counter_dashboard')
    assert response.status_code == 200
    assert b'Counter Dashboard' in response.data

def test_booking_cancellation(client, db_connection):
    """
    Test booking cancellation:
    1. Insert a booking.
    2. Set counter user in session.
    3. Send cancellation request.
    4. Verify redirect to counter dashboard.
    """
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
    """
    Test schedule update:
    1. Insert a schedule.
    2. Set counter user in session.
    3. Post update form.
    4. Verify redirect to counter dashboard.
    """
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
    """
    Test viewing user's bookings:
    1. Insert a booking for a test user.
    2. Set user in session.
    3. Access 'my bookings' page.
    4. Verify bookings are shown.
    """
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
    """
    Test user logout:
    1. Set user in session.
    2. Send logout request.
    3. Verify redirect to home.
    4. Verify session cleared.
    """
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'Test User'

    response = client.get('/logout')
    assert response.status_code == 302
    assert '/' in response.headers['Location']

    with client.session_transaction() as sess:
        assert 'user_id' not in sess

# -----------------------------
# Run tests
# -----------------------------
if __name__ == '__main__':
    pytest.main([__file__])
