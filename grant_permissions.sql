-- Grant schema privileges to wfd_user
GRANT USAGE ON SCHEMA public TO wfd_user;
GRANT CREATE ON SCHEMA public TO wfd_user;

-- Grant default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO wfd_user;

-- Verify permissions
SELECT grantee, privilege_type 
FROM role_table_grants 
WHERE table_schema='public' AND grantee='wfd_user' 
LIMIT 1;
