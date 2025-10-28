from flask import Flask, render_template, request, redirect, url_for, session
from db_config import create_connection, close_connection

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'my_serect_key_12345'  # TODO: Use a secure secret key in production

def get_start_locations():
    """Fetch unique start locations from the Route table."""
    connection = create_connection()
    locations = []
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT DISTINCT start FROM Route")
            results = cursor.fetchall()
            locations = [row[0] for row in results]
        except Exception as e:
            print(f"Error fetching start locations: {e}")
        finally:
            close_connection(connection)
    return locations

def get_destination_locations():
    """Fetch unique destination locations from the Route table."""
    connection = create_connection()
    locations = []
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT DISTINCT destination FROM Route")
            results = cursor.fetchall()
            locations = [row[0] for row in results]
        except Exception as e:
            print(f"Error fetching destination locations: {e}")
        finally:
            close_connection(connection)
    return locations

def get_available_buses(from_location, to_location, travel_date):
    """Fetch available buses for the selected route."""
    connection = create_connection()
    buses = []
    if connection:
        try:
            cursor = connection.cursor()
            query = """
                SELECT o.company_name, s.bus_no, r.start, r.destination, s.reporting_time, s.travel_time, s.ticket_price
                FROM Schedule s
                JOIN Bus b ON s.bus_no = b.bus_no
                JOIN Operator o ON b.operator_id = o.operator_id
                JOIN Route r ON s.route_id = r.route_id
                WHERE r.start = %s AND r.destination = %s
                ORDER BY s.travel_time
            """
            cursor.execute(query, (from_location, to_location))
            results = cursor.fetchall()
            for row in results:
                bus = {
                    'operator_name': row[0],
                    'bus_no': row[1],
                    'start': row[2],
                    'destination': row[3],
                    'reporting_time': str(row[4]),
                    'departure_time': str(row[5]),
                    'departure_date': travel_date,
                    'price': row[6]
                }
                buses.append(bus)
        except Exception as e:
            print(f"Error fetching available buses: {e}")
        finally:
            close_connection(connection)
    return buses

@app.route('/')
def home():
    user_type = session.get('user_type')
    if user_type == 'counter':
        return redirect(url_for('counter_dashboard'))

    start_locations = get_start_locations()
    dest_locations = get_destination_locations()
    user_name = session.get('user_name')
    message = session.pop('message', None)  # Get and remove the message from session
    return render_template('index.html', start_locations=start_locations, dest_locations=dest_locations, user_name=user_name, user_type=user_type, message=message)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('username')  # Now username is phone
        password = request.form.get('password')

        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                query = "SELECT user_id, name, user_type FROM UserAccount WHERE phone = %s AND password = %s"
                cursor.execute(query, (phone, password))
                user = cursor.fetchone()
                if user:
                    session['user_id'] = user[0]
                    session['user_name'] = user[1]
                    session['user_type'] = user[2].lower()
                    if user[2].lower() == 'counter':
                        return redirect(url_for('counter_dashboard'))
                    else:
                        return redirect(url_for('home'))
                else:
                    # TODO: Handle invalid login
                    pass
            except Exception as e:
                print(f"Error logging in: {e}")
            finally:
                close_connection(connection)
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type')

        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                query = """
                    INSERT INTO UserAccount (name, phone, email, password, user_type)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(query, (name, phone, email, password, user_type))
                connection.commit()
                return redirect(url_for('login'))
            except Exception as e:
                print(f"Error registering user: {e}")
                # TODO: Handle error (e.g., duplicate email/phone)
            finally:
                close_connection(connection)
    return render_template('register.html')

@app.route('/book', methods=['POST'])
def book():
    from_location = request.form.get('from')
    to_location = request.form.get('to')
    travel_date = request.form.get('date')

    if not from_location or not to_location or not travel_date:
        return redirect(url_for('home'))

    buses = get_available_buses(from_location, to_location, travel_date)

    return render_template('schedule.html',
                         from_location=from_location,
                         to_location=to_location,
                         travel_date=travel_date,
                         buses=buses)

@app.route('/booking', methods=['POST'])
def booking():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    bus_no = request.form.get('bus_no')

    # Fetch bus details including number of seats
    connection = create_connection()
    bus = None
    num_seats = 0
    schedule_id = None
    if connection:
        try:
            cursor = connection.cursor()
            query = """
                SELECT s.available_seats, o.company_name, r.start, r.destination, s.reporting_time, s.travel_time, s.ticket_price, s.schedule_id
                FROM Schedule s
                JOIN Bus b ON s.bus_no = b.bus_no
                JOIN Operator o ON b.operator_id = o.operator_id
                JOIN Route r ON s.route_id = r.route_id
                WHERE s.bus_no = %s
            """
            cursor.execute(query, (bus_no,))
            result = cursor.fetchone()
            if result:
                num_seats = result[0]
                schedule_id = result[7]
                bus = {
                    'bus_no': bus_no,
                    'operator_name': result[1],
                    'start': result[2],
                    'destination': result[3],
                    'departure_time': str(result[5]),
                    'departure_date': request.form.get('departure_date'),
                    'price': result[6]
                }
        except Exception as e:
            print(f"Error fetching bus details: {e}")
        finally:
            close_connection(connection)

    if not bus:
        return redirect(url_for('home'))  # Bus not found

    # Get already booked seats for this schedule
    booked_seats = set()
    if schedule_id:
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                query = "SELECT seat_no FROM Booking WHERE schedule_id = %s AND status = 'Confirmed'"
                cursor.execute(query, (schedule_id,))
                results = cursor.fetchall()
                booked_seats = {row[0] for row in results}
            except Exception as e:
                print(f"Error fetching booked seats: {e}")
            finally:
                close_connection(connection)

    # Generate seat data based on number of seats
    seats = []
    for i in range(1, num_seats + 1):
        status = 'booked' if i in booked_seats else 'available'
        seats.append({'number': i, 'status': status})

    return render_template('booking.html', bus=bus, seats=seats)

@app.route('/confirm_booking', methods=['POST'])
def confirm_booking():
    bus_no = request.form.get('bus_no')
    num_seats = int(request.form.get('num_seats'))
    selected_seats = request.form.get('selected_seats')
    from_location = request.form.get('from_location')
    to_location = request.form.get('to_location')
    travel_date = request.form.get('travel_date')

    # Fetch bus details again for display
    connection = create_connection()
    bus = None
    if connection:
        try:
            cursor = connection.cursor()
            query = """
                SELECT o.company_name, r.start, r.destination, s.travel_time, s.ticket_price
                FROM Schedule s
                JOIN Bus b ON s.bus_no = b.bus_no
                JOIN Operator o ON b.operator_id = o.operator_id
                JOIN Route r ON s.route_id = r.route_id
                WHERE s.bus_no = %s
            """
            cursor.execute(query, (bus_no,))
            result = cursor.fetchone()
            if result:
                bus = {
                    'bus_no': bus_no,
                    'operator_name': result[0],
                    'start': result[1],
                    'destination': result[2],
                    'departure_time': str(result[3]),
                    'departure_date': travel_date,
                    'price': result[4]
                }
        except Exception as e:
            print(f"Error fetching bus details: {e}")
        finally:
            close_connection(connection)

    if not bus:
        return redirect(url_for('home'))  # Bus not found

    total_price = num_seats * bus['price']

    return render_template('booking_details.html',
                         bus=bus,
                         selected_seats=selected_seats,
                         num_seats=num_seats,
                         total_price=total_price)

@app.route('/process_booking', methods=['POST'])
def process_booking():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    bus_no = request.form.get('bus_no')
    selected_seats = request.form.get('selected_seats')
    num_seats = int(request.form.get('num_seats'))
    from_location = request.form.get('from_location')
    to_location = request.form.get('to_location')
    travel_date = request.form.get('travel_date')

    print(f"Debug: bus_no={bus_no}, selected_seats={selected_seats}, num_seats={num_seats}")

    # Get passenger details
    names = request.form.getlist('name[]')
    phones = request.form.getlist('phone[]')
    cids = request.form.getlist('cid[]')

    print(f"Debug: names={names}, phones={phones}, cids={cids}")

    # Get user_id from session
    user_id = session['user_id']

    # Get schedule_id from Schedule table
    connection = create_connection()
    schedule_id = None
    if connection:
        try:
            cursor = connection.cursor()
            query = "SELECT schedule_id FROM Schedule WHERE bus_no = %s"
            cursor.execute(query, (bus_no,))
            result = cursor.fetchone()
            if result:
                schedule_id = result[0]
                print(f"Debug: Found schedule_id={schedule_id}")
            else:
                print(f"Debug: No schedule found for bus_no={bus_no}")
        except Exception as e:
            print(f"Error fetching schedule_id: {e}")
        finally:
            close_connection(connection)

    if not schedule_id:
        # Handle error: schedule not found
        print("Schedule not found")
        session['message'] = 'Error: Schedule not found for the selected bus.'
        return redirect(url_for('home'))

    # Insert bookings into database
    print(f"Debug: selected_seats={selected_seats}, names={names}, cids={cids}, phones={phones}")
    seat_list = selected_seats.split(',')
    connection = create_connection()
    booking_success = False
    if connection:
        try:
            cursor = connection.cursor()
            for i, seat in enumerate(seat_list):
                seat_no = int(seat)
                # Check if seat is already booked
                cursor.execute("SELECT COUNT(*) FROM Booking WHERE schedule_id = %s AND seat_no = %s AND status = 'Confirmed'", (schedule_id, seat_no))
                if cursor.fetchone()[0] > 0:
                    raise Exception(f'Seat {seat_no} already booked')
                # Update available seats
                cursor.execute("UPDATE Schedule SET available_seats = available_seats - 1 WHERE schedule_id = %s", (schedule_id,))
                # Insert booking
                cursor.execute("INSERT INTO Booking (user_id, schedule_id, seat_no, seats_booked, passenger_name, passenger_cid, phone, status) VALUES (%s, %s, %s, 1, %s, %s, %s, 'Confirmed')", (user_id, schedule_id, seat_no, names[i], int(cids[i]), int(phones[i])))
            connection.commit()
            booking_success = True
            print(f"Booking completed for bus {bus_no}: seats {selected_seats}")
        except Exception as e:
            print(f"Error saving booking: {e}")
            connection.rollback()
            session['message'] = f'Error saving booking: {str(e)}'
        finally:
            close_connection(connection)

    if booking_success:
        session['message'] = f'Booking successful! Seats {selected_seats} for bus {bus_no} have been confirmed.'

    # Redirect based on user type
    if session.get('user_type') == 'counter':
        return redirect(url_for('home'))  # Redirect to index for counter users
    else:
        return redirect(url_for('home'))

@app.route('/counter_dashboard')
def counter_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'counter':
        return redirect(url_for('home'))

    # Get search parameters
    search_query = request.args.get('search', '')
    status_filter = request.args.get('status', '')

    print(f"Debug: counter_dashboard called for user_id {session['user_id']}, search='{search_query}', status='{status_filter}'")

    # Fetch recent bookings with search and filter
    connection = create_connection()
    bookings = []
    total_bookings = 0
    total_confirmed_bookings = 0
    total_cancelled_bookings = 0
    total_revenue = 0
    available_seats = 0

    if connection:
        try:
            cursor = connection.cursor()

            # Build query for bookings
            query = """
                SELECT b.booking_id, b.passenger_name, b.seat_no, b.status, ua.user_type,
                       s.bus_no, r.start, r.destination, s.ticket_price,
                       b.booked_at, b.phone,
                       ua.name as booked_by_name
                FROM Booking b
                JOIN Schedule s ON b.schedule_id = s.schedule_id
                JOIN Route r ON s.route_id = r.route_id
                LEFT JOIN UserAccount ua ON b.user_id = ua.user_id
                WHERE 1=1
            """
            params = []

            if search_query:
                query += " AND (b.passenger_name LIKE %s OR ua.name LIKE %s OR s.bus_no LIKE %s)"
                params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])

            if status_filter:
                query += " AND b.status = %s"
                params.append(status_filter)

            query += " ORDER BY b.booking_id DESC LIMIT 50"

            cursor.execute(query, params)
            results = cursor.fetchall()

            for row in results:
                bookings.append({
                    'booking_id': row[0],
                    'passenger_name': row[1],
                    'passenger_phone': row[10],
                    'seat_no': row[2],
                    'status': row[3],
                    'user_type': row[4],
                    'bus_no': row[5],
                    'route': f"{row[6]} - {row[7]}",
                    'price': row[8],
                    'booking_date': row[9].strftime('%Y-%m-%d %H:%M:%S') if row[9] else 'N/A',
                    'booked_by': row[11] or 'Counter'
                })

            # Get statistics from all bookings
            cursor.execute("SELECT COUNT(*) FROM Booking")
            total_bookings = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM Booking WHERE status = 'Confirmed'")
            confirmed_bookings_result = cursor.fetchone()
            total_confirmed_bookings = confirmed_bookings_result[0] if confirmed_bookings_result else 0

            cursor.execute("SELECT COUNT(*) FROM Booking WHERE status = 'Cancelled'")
            cancelled_bookings_result = cursor.fetchone()
            total_cancelled_bookings = cancelled_bookings_result[0] if cancelled_bookings_result else 0

            cursor.execute("SELECT SUM(s.ticket_price) FROM Booking b JOIN Schedule s ON b.schedule_id = s.schedule_id WHERE b.status = 'Confirmed'")
            revenue_result = cursor.fetchone()
            total_revenue = revenue_result[0] if revenue_result and revenue_result[0] else 0

            # Calculate available seats (simplified)
            cursor.execute("SELECT SUM(available_seats) FROM Schedule")
            seats_result = cursor.fetchone()
            available_seats = seats_result[0] if seats_result[0] else 0

            print(f"Debug: Stats - total: {total_bookings}, confirmed: {total_confirmed_bookings}, cancelled: {total_cancelled_bookings}, revenue: {total_revenue}")

        except Exception as e:
            print(f"Error fetching dashboard data: {e}")
        finally:
            close_connection(connection)

    return render_template('counter_dashboard.html',
                         bookings=bookings,
                         total_bookings=total_bookings,
                         total_confirmed_bookings=total_confirmed_bookings,
                         total_cancelled_bookings=total_cancelled_bookings,
                         total_revenue=total_revenue,
                         available_seats=available_seats,
                         search_query=search_query,
                         status_filter=status_filter)

@app.route('/book_on_behalf')
def book_on_behalf():
    if 'user_id' not in session or session.get('user_type') != 'counter':
        return redirect(url_for('home'))

    start_locations = get_start_locations()
    dest_locations = get_destination_locations()
    user_name = session.get('user_name')
    message = session.pop('message', None)  # Get and remove the message from session

    return render_template('index.html',
                         start_locations=start_locations,
                         dest_locations=dest_locations,
                         user_name=user_name,
                         user_type='counter',
                         message=message)

@app.route('/process_counter_booking', methods=['POST'])
def process_counter_booking():
    if 'user_id' not in session or session.get('user_type') != 'counter':
        return redirect(url_for('home'))

    # Get form data
    customer_name = request.form.get('customer_name')
    customer_phone = request.form.get('customer_phone')
    from_location = request.form.get('from')
    to_location = request.form.get('to')
    travel_date = request.form.get('date')
    bus_no = request.form.get('bus_no')
    num_seats = int(request.form.get('num_seats'))

    # Get passenger details
    names = request.form.getlist('name[]')
    phones = request.form.getlist('phone[]')
    cids = request.form.getlist('cid[]')

    # Get schedule_id
    connection = create_connection()
    schedule_id = None
    if connection:
        try:
            cursor = connection.cursor()
            query = "SELECT schedule_id FROM Schedule WHERE bus_no = %s"
            cursor.execute(query, (bus_no,))
            result = cursor.fetchone()
            if result:
                schedule_id = result[0]
        except Exception as e:
            print(f"Error fetching schedule_id: {e}")
        finally:
            close_connection(connection)

    if not schedule_id:
        session['message'] = 'Error: Schedule not found for the selected bus.'
        return redirect(url_for('book_on_behalf'))

    # Insert bookings into database
    connection = create_connection()
    booking_success = False
    if connection:
        try:
            cursor = connection.cursor()
            for i in range(num_seats):
                # Find next available seat (simplified - in real app, you'd check availability)
                seat_no = i + 1  # This is simplified; real implementation should check available seats

                # Check if seat is already booked
                cursor.execute("""
                    SELECT COUNT(*) FROM Booking
                    WHERE schedule_id = %s AND seat_no = %s AND status = 'Confirmed'
                """, (schedule_id, seat_no))
                booked_count = cursor.fetchone()[0]

                if booked_count == 0:
                    # Update available seats
                    cursor.execute("""
                        UPDATE Schedule
                        SET available_seats = available_seats - 1
                        WHERE schedule_id = %s
                    """, (schedule_id,))

                    # Insert booking
                    cursor.execute("""
                        INSERT INTO Booking(user_id, schedule_id, seat_no, seats_booked,
                                           passenger_name, passenger_cid, phone, status)
                        VALUES(%s, %s, %s, 1, %s, %s, %s, %s)
                    """, (session['user_id'], schedule_id, seat_no, names[i], int(cids[i]), int(phones[i])))
                else:
                    raise Exception(f'Seat {seat_no} already booked')

            connection.commit()
            booking_success = True
        except Exception as e:
            print(f"Error saving booking: {e}")
            connection.rollback()
            session['message'] = f'Error saving booking: {str(e)}'
        finally:
            close_connection(connection)

    if booking_success:
        session['message'] = f'Booking successful! {num_seats} seats booked for customer {customer_name}.'

    return redirect(url_for('counter_dashboard'))

@app.route('/manage_bookings')
def manage_bookings():
    if 'user_id' not in session or session.get('user_type') != 'counter':
        return redirect(url_for('home'))

    # Similar to counter_dashboard but with more management features
    return redirect(url_for('counter_dashboard'))

@app.route('/cancel_booking/<int:booking_id>')
def cancel_booking(booking_id):
    if 'user_id' not in session or session.get('user_type') != 'counter':
        return redirect(url_for('home'))

    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("UPDATE Booking SET status = 'Cancelled' WHERE booking_id = %s", (booking_id,))
            connection.commit()
            session['message'] = f'Booking {booking_id} has been cancelled successfully.'
        except Exception as e:
            print(f"Error cancelling booking: {e}")
            session['message'] = 'Error cancelling booking.'
        finally:
            close_connection(connection)

    return redirect(url_for('counter_dashboard'))

@app.route('/confirm_pending_booking/<int:booking_id>')
def confirm_pending_booking(booking_id):
    if 'user_id' not in session or session.get('user_type') != 'counter':
        return redirect(url_for('home'))

    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("UPDATE Booking SET status = 'Confirmed' WHERE booking_id = %s", (booking_id,))
            connection.commit()
            session['message'] = f'Booking {booking_id} has been confirmed successfully.'
        except Exception as e:
            print(f"Error confirming booking: {e}")
            session['message'] = 'Error confirming booking.'
        finally:
            close_connection(connection)

    return redirect(url_for('counter_dashboard'))

@app.route('/my_bookings')
def my_bookings():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    print(f"Debug: my_bookings called for user_id {user_id}")

    # Fetch user's bookings
    connection = create_connection()
    bookings = []
    if connection:
        try:
            cursor = connection.cursor()
            query = """
                SELECT b.booking_id, b.passenger_name, b.seat_no, b.status, ua.user_type,
                       s.bus_no, r.start, r.destination, s.ticket_price,
                       b.booked_at, b.phone, b.passenger_cid, s.reporting_time, s.travel_time
                FROM Booking b
                JOIN Schedule s ON b.schedule_id = s.schedule_id
                JOIN Route r ON s.route_id = r.route_id
                JOIN UserAccount ua ON b.user_id = ua.user_id
                WHERE b.user_id = %s
                ORDER BY b.booked_at DESC
            """
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()
            print(f"Debug: Found {len(results)} bookings for user {user_id}")

            for row in results:
                bookings.append({
                    'booking_id': row[0],
                    'passenger_name': row[1],
                    'seat_no': row[2],
                    'status': row[3],
                    'user_type': row[4],
                    'bus_no': row[5],
                    'route': f"{row[6]} - {row[7]}",
                    'price': row[8],
                    'booking_date': row[9].strftime('%Y-%m-%d %H:%M:%S') if row[9] else 'N/A',
                    'passenger_phone': row[10],
                    'passenger_cid': row[11],
                    'reporting_time': str(row[12]) if row[12] else 'N/A',
                    'departure_time': str(row[13]) if row[13] else 'N/A'
                })
        except Exception as e:
            print(f"Error fetching user bookings: {e}")
        finally:
            close_connection(connection)

    return render_template('my_bookings.html', bookings=bookings)

@app.route('/update_schedule', methods=['GET', 'POST'])
def update_schedule():
    if 'user_id' not in session or session.get('user_type') != 'counter':
        return redirect(url_for('home'))

    if request.method == 'POST':
        schedule_id = request.form.get('schedule_id')
        departure_time = request.form.get('departure_time')
        arrival_time = request.form.get('arrival_time')

        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                # Update Schedule table
                cursor.execute("""
                    UPDATE Schedule
                    SET travel_time = %s, reporting_time = %s
                    WHERE schedule_id = %s
                """, (departure_time, arrival_time, int(schedule_id)))
                # Update related bookings to 'Rescheduled'
                cursor.execute("""
                    UPDATE Booking
                    SET status = 'Rescheduled'
                    WHERE schedule_id = %s
                """, (int(schedule_id),))
                connection.commit()
                session['message'] = 'Schedule updated successfully. All related bookings have been marked as rescheduled.'
            except Exception as e:
                print(f"Error updating schedule: {e}")
                session['message'] = f'Error updating schedule: {str(e)}'
            finally:
                close_connection(connection)

        return redirect(url_for('counter_dashboard'))

    # GET request - show schedule update form
    connection = create_connection()
    schedules = []
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT s.schedule_id, s.bus_no, r.start, r.destination, s.travel_time, s.reporting_time
                FROM Schedule s
                JOIN Route r ON s.route_id = r.route_id
                ORDER BY s.bus_no
            """)
            results = cursor.fetchall()
            for row in results:
                schedules.append({
                    'schedule_id': row[0],
                    'bus_no': row[1],
                    'route': f"{row[2]} - {row[3]}",
                    'departure_time': str(row[4]),
                    'arrival_time': str(row[5])
                })
        except Exception as e:
            print(f"Error fetching schedules: {e}")
        finally:
            close_connection(connection)

    return render_template('update_schedule.html', schedules=schedules)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
