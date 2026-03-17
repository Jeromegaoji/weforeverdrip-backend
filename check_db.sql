-- Check if wfd_db exists
SELECT datname FROM pg_database WHERE datname='wfd_db';

-- Check if wfd_user exists
SELECT usename FROM pg_user WHERE usename='wfd_user';
