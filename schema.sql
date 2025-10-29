CREATE DATABASE DrRide_db;
USE DrRide_db;



/* ================== Route table ===================*/
CREATE TABLE Route (
    route_id INT AUTO_INCREMENT PRIMARY KEY,
    start VARCHAR(50) NOT NULL,
    destination VARCHAR(50) NOT NULL,
    distance DECIMAL(6,2) NOT NULL CHECK (distance BETWEEN 5 AND 500)
);
INSERT INTO Route (start, destination, distance) VALUES
('Thimphu', 'Paro', 55.00), ('Paro', 'Thimphu', 55.00), ('Thimphu', 'Punakha', 72.00), ('Punakha', 'Thimphu', 72.00),('Thimphu', 'Haa', 115.00), ('Haa', 'Thimphu', 115.00),('Thimphu', 'Wangdue Phodrang', 70.00), ('Wangdue Phodrang', 'Thimphu', 70.00), 
('Wangdue Phodrang', 'Trongsa', 129.00),('Trongsa', 'Wangdue Phodrang', 129.00), ('Trongsa', 'Bumthang', 68.00), ('Bumthang', 'Trongsa', 68.00), ('Bumthang', 'Zhemgang', 100.00), ('Zhemgang', 'Bumthang', 100.00), ('Bumthang', 'Mongar', 198.00), 
('Mongar', 'Bumthang', 198.00), ('Mongar', 'Trashigang', 91.00), ('Trashigang', 'Mongar', 91.00), ('Trashigang', 'Trashiyangtse', 53.00), ('Trashiyangtse', 'Trashigang', 53.00), ('Mongar', 'Lhuentse', 76.00), ('Lhuentse', 'Mongar', 76.00), ('Thimphu', 'Phuentsholing', 170.00), 
('Phuentsholing', 'Thimphu', 170.00), ('Phuentsholing', 'Chukha', 85.00), ('Chukha', 'Phuentsholing', 85.00), ('Chukha', 'Thimphu', 155.00), ('Thimphu', 'Chukha', 155.00), ('Samtse', 'Phuentsholing', 155.00), ('Phuentsholing', 'Samtse', 155.00), ('Samtse', 'Dagana', 130.00), 
('Dagana', 'Samtse', 130.00), ('Dagana', 'Tsirang', 80.00), ('Tsirang', 'Dagana', 80.00), ('Tsirang', 'Sarpang', 64.00), ('Sarpang', 'Tsirang', 64.00), ('Sarpang', 'Gelephu', 30.00), ('Gelephu', 'Sarpang', 30.00), ('Sarpang', 'Zhemgang', 145.00), ('Zhemgang', 'Sarpang', 145.00), 
('Samdrup Jongkhar', 'Trashigang', 180.00), ('Trashigang', 'Samdrup Jongkhar', 180.00), ('Samdrup Jongkhar', 'Pemagatshel', 85.00), ('Pemagatshel', 'Samdrup Jongkhar', 85.00);
SELECT *FROM Route;

/* ========================Operator Table ==================================*/
CREATE TABLE Operator (
    operator_id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    contact_info VARCHAR(200)
);
INSERT INTO Operator (company_name, contact_info) VALUES
('Bumpa Transport Service', '17867890'), ('Dhug Transport Service', '17912345'), ('Khorlo Transport Service', '17754321'), 
('Meto Transport Service', '17698765'), ('Sernya', '17543210');

SELECT * FROM Operator;


/*=============================Bus Table ==================================*/
CREATE TABLE Bus (
    bus_no VARCHAR(20) PRIMARY KEY,
    operator_id INT NOT NULL,
    capacity INT NOT NULL CHECK (capacity > 0),
    FOREIGN KEY (operator_id) REFERENCES Operator(operator_id)
        ON DELETE CASCADE
);

INSERT INTO Bus (bus_no, operator_id, capacity) VALUES
-- BP-1: Phuentsholing – Thimphu
('BP-1-A1088', 1, 19),  -- Bumpa
('BP-1-B1802', 2, 32),  -- Dhug
('BP-1-A1903', 3, 19),  -- Khorlo
-- BP-2: Thimphu – Paro
('BP-2-A2001', 4, 19),  -- Meto
('BP-2-B2002', 5, 19),  -- Sernya
-- BP-1: Thimphu – Punakha
('BP-1-A1004', 1, 19),  -- Bumpa
('BP-1-B1005', 3, 32),  -- Khorlo
-- BP-2: Thimphu – Haa
('BP-2-A2003', 2, 32),  -- Dhug
-- BP-1: Wangdue – Trongsa
('BP-1-A1006', 1, 19),  -- Bumpa
('BP-1-B1007', 4, 32),  -- Meto
-- BP-2: Trongsa – Bumthang
('BP-2-A2004', 3, 32),  -- Khorlo
('BP-2-B2005', 5, 19),  -- Sernya
-- BP-1: Bumthang – Mongar
('BP-1-A1008', 1, 32),  -- Bumpa
('BP-1-B1009', 2, 32),  -- Dhug
-- BP-2: Mongar – Trashigang
('BP-2-A2006', 4, 32),  -- Meto
('BP-2-B2007', 5, 28),  -- Sernya
-- BP-1: Trashigang – Trashiyangtse
('BP-1-A1010', 3, 28),  -- Khorlo
-- BP-2: Mongar – Lhuentse
('BP-2-A2008', 2, 28),  -- Dhug
-- BP-1: Phuentsholing – Chukha
('BP-1-B1011', 1, 32),  -- Bumpa
-- BP-2: Chukha – Thimphu
('BP-2-A2009', 5, 32),  -- Sernya
-- BP-1: Samtse – Phuentsholing
('BP-1-B1012', 2, 19),  -- Dhug
('BP-1-A1013', 3, 28),  -- Khorlo
-- BP-2: Samtse – Dagana
('BP-2-B2010', 4, 19),  -- Meto
-- BP-1: Dagana – Tsirang
('BP-1-A1014', 1, 32),  -- Bumpa
-- BP-2: Tsirang – Sarpang
('BP-2-B2011', 2, 28),  -- Dhug
-- BP-1: Sarpang – Gelephu
('BP-1-A1015', 5, 28),  -- Sernya
-- BP-2: Sarpang – Zhemgang
('BP-2-B2012', 4, 19),  -- Meto
-- BP-1: Samdrup Jongkhar – Trashigang
('BP-1-A1016', 1, 19),  -- Bumpa
('BP-1-B1017', 2, 32),  -- Dhug
-- BP-2: Samdrup Jongkhar – Pemagatshel
('BP-2-A2013', 3, 32);  -- Khorlo













/* ======================= Schedule Table =========================*/
CREATE TABLE Schedule (
    schedule_id INT AUTO_INCREMENT PRIMARY KEY,
    bus_no VARCHAR(20) NOT NULL,
    route_id INT NOT NULL,
    reporting_time  TIME NOT NULL,
    travel_time TIME NOT NULL,
    available_seats INT NOT NULL CHECK (available_seats >= 0),
    FOREIGN KEY (bus_no) REFERENCES Bus(bus_no)
        ON DELETE CASCADE,
    FOREIGN KEY (route_id) REFERENCES Route(route_id)
        ON DELETE CASCADE,
    UNIQUE (bus_no, travel_time)
);
INSERT INTO Schedule (bus_no, route_id, reporting_time, travel_time, available_seats) VALUES
-- BP-1: Phuentsholing – Thimphu
('BP-1-A1088', 23, '06:30:00', '07:00:00', 19),  -- Bumpa
('BP-1-B1802', 23, '11:00:00', '11:30:00', 32),  -- Dhug
('BP-1-A1903', 23, '14:00:00', '14:30:00', 19),  -- Khorlo
-- BP-2: Thimphu – Paro
('BP-2-A2001', 1, '08:30:00', '09:00:00', 19),  -- Meto
('BP-2-B2002', 2, '13:30:00', '14:00:00', 19),  -- Sernya
-- BP-1: Thimphu – Punakha
('BP-1-A1004', 3, '09:30:00', '10:00:00', 19),  -- Bumpa
('BP-1-B1005', 3, '13:00:00', '13:30:00', 32),  -- Khorlo
-- BP-2: Thimphu – Haa
('BP-2-A2003', 5, '07:00:00', '07:30:00', 32),  -- Dhug
-- BP-1: Wangdue – Trongsa
('BP-1-A1006', 9, '07:30:00', '08:00:00', 19),  -- Bumpa
('BP-1-B1007', 9, '08:30:00', '09:00:00', 32),  -- Meto
-- BP-2: Trongsa – Bumthang
('BP-2-A2004', 11, '10:30:00', '11:00:00', 32),  -- Khorlo
('BP-2-B2005', 11, '12:00:00', '12:30:00', 19),  -- Sernya
-- BP-1: Bumthang – Mongar
('BP-1-A1008', 15, '07:30:00', '08:00:00', 32),  -- Bumpa
('BP-1-B1009', 15, '08:30:00', '09:00:00', 32),  -- Dhug
-- BP-2: Mongar – Trashigang
('BP-2-A2006', 17, '06:30:00', '07:00:00', 32),  -- Meto
('BP-2-B2007', 17, '07:00:00', '07:30:00', 28),  -- Sernya
-- BP-1: Trashigang – Trashiyangtse
('BP-1-A1010', 19, '08:00:00', '08:30:00', 28),  -- Khorlo
-- BP-2: Mongar – Lhuentse
('BP-2-A2008', 21, '09:30:00', '10:00:00', 28),  -- Dhug
-- BP-1: Phuentsholing – Chukha
('BP-1-B1011', 25, '06:30:00', '07:00:00', 32),  -- Bumpa
-- BP-2: Chukha – Thimphu
('BP-2-A2009', 27, '06:30:00', '07:00:00', 32),  -- Sernya
-- BP-1: Samtse – Phuentsholing
('BP-1-B1012', 29, '05:30:00', '06:00:00', 19),  -- Dhug
('BP-1-A1013', 29, '07:30:00', '08:00:00', 28),  -- Khorlo
-- BP-2: Samtse – Dagana
('BP-2-B2010', 31, '09:30:00', '10:00:00', 19),  -- Meto
-- BP-1: Dagana – Tsirang
('BP-1-A1014', 33, '10:30:00', '11:00:00', 32),  -- Bumpa
-- BP-2: Tsirang – Sarpang
('BP-2-B2011', 35, '10:00:00', '10:30:00', 28),  -- Dhug
-- BP-1: Sarpang – Gelephu
('BP-1-A1015', 37, '11:30:00', '12:00:00', 28),  -- Sernya
-- BP-2: Sarpang – Zhemgang
('BP-2-B2012', 39, '09:00:00', '09:30:00', 19),  -- Meto
-- BP-1: Samdrup Jongkhar – Trashigang
('BP-1-A1016', 41, '06:00:00', '06:30:00', 19),  -- Bumpa
('BP-1-B1017', 41, '06:30:00', '07:00:00', 32),  -- Dhug
-- BP-2: Samdrup Jongkhar – Pemagatshel
('BP-2-A2013', 43, '08:30:00', '09:00:00', 32);  -- Khorlo

ALTER TABLE Schedule
ADD COLUMN ticket_price DECIMAL(10,2);

UPDATE Schedule s
JOIN Route r ON s.route_id = r.route_id
SET s.ticket_price = 
    CASE
        WHEN r.distance <= 80 THEN r.distance * 4.5
        WHEN r.distance <= 150 THEN r.distance * 4.0
        ELSE r.distance * 3.5
    END;












/* ======================== User Table =============================*/
CREATE TABLE UserAccount (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(50) UNIQUE NOT NULL,
    user_type ENUM('Passenger','Counter') NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
SELECT * FROM UserAccount;

DELETE  FROM UserAccount
where user_id = 4;





/* ======================  Booking ===========================*/
CREATE TABLE Booking (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    schedule_id INT NOT NULL,
    seat_no INT NOT NULL,
    seats_booked INT NOT NULL CHECK (seats_booked > 0),
    passenger_name VARCHAR(150) NOT NULL,
    passenger_cid INT UNIQUE,
    phone INT,
    status ENUM('Confirmed','Cancelled') DEFAULT 'Confirmed',
    booked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES UserAccount(user_id)
        ON DELETE CASCADE,
    FOREIGN KEY (schedule_id) REFERENCES Schedule(schedule_id)
        ON DELETE CASCADE,
    UNIQUE (schedule_id, seat_no)
);
ALTER TABLE Booking
MODIFY passenger_cid BIGINT UNSIGNED NOT NULL;

ALTER TABLE Booking
MODIFY status VARCHAR(20) NOT NULL DEFAULT 'Confirmed';

SELECT * FROM Booking;


delete from Booking
where booking_id = 6;




