DELIMITER $$

DROP TRIGGER IF EXISTS update_schedule_trigger;

CREATE TRIGGER update_schedule_trigger
AFTER UPDATE ON Schedule
FOR EACH ROW
BEGIN
    UPDATE Booking
    SET status = 'Rescheduled'
    WHERE schedule_id = NEW.schedule_id;
END$$

DROP PROCEDURE IF EXISTS UpdateSchedule;

CREATE PROCEDURE UpdateSchedule(
    IN p_schedule_id INT,
    IN p_departure_time TIME,
    IN p_arrival_time TIME
)
BEGIN
    UPDATE Schedule
    SET travel_time = p_departure_time,
        reporting_time = p_arrival_time,
        last_updated = CURRENT_TIMESTAMP
    WHERE schedule_id = p_schedule_id;
END$$

DROP PROCEDURE IF EXISTS ProcessBooking;

CREATE PROCEDURE ProcessBooking(
    IN p_user_id INT,
    IN p_schedule_id INT,
    IN p_selected_seats VARCHAR(255),
    IN p_names VARCHAR(1000),
    IN p_cids VARCHAR(1000),
    IN p_phones VARCHAR(1000)
)
BEGIN
    DECLARE seat_no INT;
    DECLARE name VARCHAR(100);
    DECLARE cid BIGINT;
    DECLARE phone INT;
    DECLARE seat_list VARCHAR(255);
    DECLARE name_list VARCHAR(1000);
    DECLARE cid_list VARCHAR(1000);
    DECLARE phone_list VARCHAR(1000);
    DECLARE i INT DEFAULT 1;
    DECLARE seat_count INT;
    DECLARE booked_count INT;

    SET seat_list = p_selected_seats;
    SET name_list = p_names;
    SET cid_list = p_cids;
    SET phone_list = p_phones;

    SET seat_count = LENGTH(seat_list) - LENGTH(REPLACE(seat_list, ',', '')) + 1;

    START TRANSACTION;

    SELECT available_seats FROM Schedule WHERE schedule_id = p_schedule_id FOR UPDATE;

    -- Check for already booked seats to prevent duplicates
    CREATE TEMPORARY TABLE temp_seats (seat_no INT);
    SET @sql = CONCAT('INSERT INTO temp_seats (seat_no) VALUES (', REPLACE(seat_list, ',', '),('), ')');
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

    SELECT COUNT(*) INTO booked_count FROM Booking b
    JOIN temp_seats t ON b.seat_no = t.seat_no
    WHERE b.schedule_id = p_schedule_id AND b.status = 'Confirmed'
    FOR UPDATE;

    IF booked_count > 0 THEN
        DROP TEMPORARY TABLE temp_seats;
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'One or more seats already booked';
    END IF;

    DROP TEMPORARY TABLE temp_seats;

    WHILE i <= seat_count DO
        SET seat_no = CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(seat_list, ',', i), ',', -1) AS UNSIGNED);
        SET name = SUBSTRING_INDEX(SUBSTRING_INDEX(name_list, ',', i), ',', -1);
        SET cid = CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(cid_list, ',', i), ',', -1) AS UNSIGNED);
        SET phone = CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(phone_list, ',', i), ',', -1) AS UNSIGNED);

        SELECT COUNT(*) INTO booked_count FROM Booking WHERE schedule_id = p_schedule_id AND seat_no = seat_no AND status = 'Confirmed';

        IF booked_count > 0 THEN
            ROLLBACK;
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Seat already booked';
        END IF;

        UPDATE Schedule SET available_seats = available_seats - 1 WHERE schedule_id = p_schedule_id;

        INSERT INTO Booking(user_id, schedule_id, seat_no, seats_booked, passenger_name, passenger_cid, phone, status)
        VALUES(p_user_id, p_schedule_id, seat_no, 1, name, cid, phone, 'Confirmed');

        SET i = i + 1;
    END WHILE;

    COMMIT;
END$$

DELIMITER ;
