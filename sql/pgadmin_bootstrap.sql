-- Run this in pgAdmin Query Tool while connected to template1 (or any existing DB).
-- Creates/updates the app role used by Django.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sanction_user') THEN
        CREATE ROLE sanction_user LOGIN PASSWORD '1234';
    ELSE
        ALTER ROLE sanction_user WITH LOGIN PASSWORD '1234';
    END IF;
END
$$;

-- Check if the target database exists.
SELECT datname
FROM pg_database
WHERE datname = 'sanction_tracker_db';

-- If no row is returned, run this once:
-- CREATE DATABASE sanction_tracker_db OWNER sanction_user;
