"""
Grant CREATEDB permission to wfd_user for testing.
"""
import psycopg2
from psycopg2 import sql

try:
    # Connect as postgres (superuser)
    conn = psycopg2.connect(
        dbname="wfd_db",
        user="postgres",
        password="03wfd2026",
        host="localhost",
        port="5432"
    )
    conn.autocommit = True
    cursor = conn.cursor()

    # Grant CREATEDB permission
    cursor.execute("ALTER USER wfd_user CREATEDB;")
    print("✓ CREATEDB permission granted to wfd_user")

    cursor.close()
    conn.close()
except Exception as e:
    print(f"✗ Error: {e}")
