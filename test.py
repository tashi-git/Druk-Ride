import pytest
from flask import Flask, session
from app import app as flask_app  # Import the Flask app instance
from unittest.mock import patch, MagicMock
import json

# Test client for Flask app
@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test_secret_key_12345'
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client

@pytest.fixture
def mock_db_connection():
    """Mock database connection for testing."""
    with patch('app.create_connection') as mock_conn:
        mock_cursor = MagicMock()
        mock_conn.return_value = mock_cursor
        yield mock_conn, mock_cursor

# Test Case 1: Home Page Access
def test_home_page(client):
    """Test that the home page loads correctly for non-logged-in users."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'DrukRide' in response.data  # Check if the app name is in the response

# Test Case 2: User Registration
def test_user_registration(client, mock_db_connection):
    """Test user registration functionality."""
    mock_conn, mock_cursor = mock_db_connection

    # Mock successful registration
    mock_cursor.execute.return_value = None
    mock_conn.commit.return_value = None

    response = client.post('/register', data={
        'name': 'Test User',
        'phone': '1234567890',
        'email': 'test@example.com',
        'password': 'password123',
        'user_type': 'customer'
    })

    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.headers['Location']

# Test Case 3: User Login
def test_user_login(client, mock_db_connection):
    """Test user login functionality."""
    mock_conn, mock_cursor = mock_db_connection

    # Mock successful login
    mock_cursor.fetchone.return_value = (1, 'Test User', 'customer')

    response = client.post('/login', data={
        'username': '1234567890',
        'password': 'password123'
    })

    assert response.status_code == 302  # Redirect to home
    assert '/' in response.headers['Location']

# Test Case 4: Booking Search
def test_booking_search(client, mock_db_connection):
    """Test searching for available buses."""
    mock_conn, mock_cursor = mock_db_connection

    # Mock bus search results
    mock_cursor.fetchall.return_value = [
        ('Operator A', 'BUS001', 'Thimphu', 'Phuentsholing', '08:00:00', '12:00:00', 500.0)
    ]

    response = client.post('/book', data={
        'from': 'Thimphu',
        'to': 'Phuentsholing',
        'date': '2025-01-01'
    })

    assert response.status_code == 200
    assert b'Available Buses' in response.data

# Test Case 5: Seat Selection and Booking
def test_seat_booking(client, mock_db_connection):
    """Test seat selection and booking process."""
    mock_conn, mock_cursor = mock_db_connection

    # Mock bus details
    mock_cursor.fetchone.return_value = (40, 'Operator A', 'Thimphu', 'Phuentsholing', '08:00:00', '12:00:00', 500.0, 1)

    # Mock booked seats (none booked)
    mock_cursor.fetchall.return_value = []

    with client.session_transaction() as sess:
        sess['user_id'] = 1

    response = client.post('/booking', data={'bus_no': 'BUS001'})
    assert response.status_code == 200
    assert b'Select Your Seats' in response.data

# Test Case 6: Counter Dashboard Access
def test_counter_dashboard(client, mock_db_connection):
    """Test counter dashboard access for counter users."""
    mock_conn, mock_cursor = mock_db_connection

    # Mock booking data
    mock_cursor.fetchall.return_value = [
        (1, 'John Doe', 1, 'Confirmed', 'customer', 'BUS001', 'Thimphu', 'Phuentsholing', 500.0, 'Counter', None, '1234567890', '1234567890123', '08:00:00', '12:00:00')
    ]
    mock_cursor.fetchone.side_effect = [10, 8, 2, 4000.0, 100]  # Mock statistics

    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_type'] = 'counter'

    response = client.get('/counter_dashboard')
    assert response.status_code == 200
    assert b'Counter Dashboard' in response.data

# Test Case 7: Booking Cancellation
def test_booking_cancellation(client, mock_db_connection):
    """Test booking cancellation by counter."""
    mock_conn, mock_cursor = mock_db_connection

    mock_cursor.execute.return_value = None
    mock_conn.commit.return_value = None

    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_type'] = 'counter'

    response = client.get('/cancel_booking/1')
    assert response.status_code == 302  # Redirect to dashboard
    assert '/counter_dashboard' in response.headers['Location']

# Test Case 8: Schedule Update
def test_schedule_update(client, mock_db_connection):
    """Test schedule update functionality."""
    mock_conn, mock_cursor = mock_db_connection

    mock_cursor.callproc.return_value = None
    mock_conn.commit.return_value = None

    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_type'] = 'counter'

    response = client.post('/update_schedule', data={
        'schedule_id': '1',
        'departure_time': '09:00:00',
        'arrival_time': '13:00:00'
    })

    assert response.status_code == 302  # Redirect to dashboard
    assert '/counter_dashboard' in response.headers['Location']

# Test Case 9: My Bookings
def test_my_bookings(client, mock_db_connection):
    """Test viewing user's own bookings."""
    mock_conn, mock_cursor = mock_db_connection

    # Mock user's bookings
    mock_cursor.fetchall.return_value = [
        (1, 'John Doe', 1, 'Confirmed', 'customer', 'BUS001', 'Thimphu', 'Phuentsholing', 500.0, None, '1234567890', '1234567890123', '08:00:00', '12:00:00')
    ]

    with client.session_transaction() as sess:
        sess['user_id'] = 1

    response = client.get('/my_bookings')
    assert response.status_code == 200
    assert b'My Bookings' in response.data

# Test Case 10: Logout
def test_logout(client):
    """Test user logout functionality."""
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'Test User'

    response = client.get('/logout')
    assert response.status_code == 302  # Redirect to home
    assert '/' in response.headers['Location']

    # Check that session is cleared
    with client.session_transaction() as sess:
        assert 'user_id' not in sess

if __name__ == '__main__':
    pytest.main([__file__])
