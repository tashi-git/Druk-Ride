import pytest
from app import app as flask_app, create_connection

# -----------------------------
# Test client fixture
# -----------------------------
@pytest.fixture
def client():
    """Create a Flask test client."""
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
    """Return a real connection to the test database."""
    conn = create_connection(testing=True)
    cursor = conn.cursor(dictionary=True)  # JSON-serializable rows
    yield conn, cursor
    conn.rollback()  # undo changes after each test
    cursor.close()
    conn.close()

# -----------------------------
# Test Cases
# -----------------------------

# 1️⃣ Home Page
def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'DrukRide' in response.data

# 2️⃣ User Registration
def test_user_registration(client, db_connection):
    conn, cursor = db_connection
    response = client.post('/register', data={
        'name': 'Test User',
        'phone': '9998887777',
        'email': 'testuser@example.com',
        'password': 'password123',
        'user_type': 'customer'
    })
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

    # Verify user inserted
    cursor.execute("SELECT * FROM users WHERE phone='9998887777'")
    user = cursor.fetchone()
    assert user['name'] == 'Test User'

# 3️⃣ User Login
def test_user_login(client, db_connection):
    conn, cursor = db_connection
    # Insert test user
    cursor.execute("""
        INSERT INTO users (name, phone, email, password, user_type)
        VALUES ('Login User', '1112223333', 'login@example.com', 'password123', 'customer')
    """)
    conn.commit()

    response = client.post('/login', data={
        'username': '1112223333',
        'password': 'password123'
    })
    assert response.status_code == 302
    assert '/' in response.headers['Location']

# 4️⃣ Booking Search
def test_booking_search(client, db_connection):
    conn, cursor = db_connection
    # Insert test schedule
    cursor.execute("""
        INSERT INTO Schedule (bus_no, route_id, reporting_time, travel_time, available_seats, ticket_price)
        VALUES ('TEST001', 1, '08:00:00', '12:00:00', 40, 500)
    """)
    conn.commit()

    response = client.post('/book', data={
        'from': 'Thimphu',
        'to': 'Phuentsholing',
        'date': '2025-01-01'
    })
    assert response.status_code == 200
    assert b'Available Buses' in response.data

# 5️⃣ Seat Booking
def test_seat_booking(client, db_connection):
    conn, cursor = db_connection
    # Insert schedule for booking
    cursor.execute("""
        INSERT INTO Schedule (bus_no, route_id, reporting_time, travel_time, available_seats, ticket_price)
        VALUES ('BOOK001', 1, '08:00:00', '12:00:00', 40, 500)
    """)
    conn.commit()

    with client.session_transaction() as sess:
        sess['user_id'] = 1

    response = client.post('/booking', data={'bus_no': 'BOOK001'})
    assert response.status_code == 200
    assert b'Select Your Seats' in response.data

# 6️⃣ Counter Dashboard
def test_counter_dashboard(client, db_connection):
    conn, cursor = db_connection
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_type'] = 'counter'

    response = client.get('/counter_dashboard')
    assert response.status_code == 200
    assert b'Counter Dashboard' in response.data

# 7️⃣ Booking Cancellation
def test_booking_cancellation(client, db_connection):
    conn, cursor = db_connection
    # Insert test booking
    cursor.execute("""
        INSERT INTO Booking (user_id, schedule_id, status)
        VALUES (1, 1, 'Confirmed')
    """)
    conn.commit()

    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_type'] = 'counter'

    response = client.get('/cancel_booking/1')
    assert response.status_code == 302
    assert '/counter_dashboard' in response.headers['Location']

# 8️⃣ Schedule Update
def test_schedule_update(client, db_connection):
    conn, cursor = db_connection
    cursor.execute("""
        INSERT INTO Schedule (bus_no, route_id, reporting_time, travel_time, available_seats, ticket_price)
        VALUES ('UPD001', 1, '08:00:00', '12:00:00', 40, 500)
    """)
    conn.commit()

    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_type'] = 'counter'

    response = client.post('/update_schedule', data={
        'schedule_id': 1,
        'departure_time': '09:00:00',
        'arrival_time': '13:00:00'
    })
    assert response.status_code == 302
    assert '/counter_dashboard' in response.headers['Location']

# 9️⃣ My Bookings
def test_my_bookings(client, db_connection):
    conn, cursor = db_connection
    cursor.execute("""
        INSERT INTO Booking (user_id, schedule_id, status)
        VALUES (1, 1, 'Confirmed')
    """)
    conn.commit()

    with client.session_transaction() as sess:
        sess['user_id'] = 1

    response = client.get('/my_bookings')
    assert response.status_code == 200
    assert b'My Bookings' in response.data

# 🔟 Logout
def test_logout(client):
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
