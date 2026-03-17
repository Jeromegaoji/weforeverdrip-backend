-- Create wfd_user if it doesn't exist
CREATE USER wfd_user WITH PASSWORD '03wfd2026';

-- Grant all privileges on wfd_db to wfd_user
GRANT ALL PRIVILEGES ON DATABASE wfd_db TO wfd_user;

-- Verify user was created
SELECT usename FROM pg_user WHERE usename='wfd_user';
