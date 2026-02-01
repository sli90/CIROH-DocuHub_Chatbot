import os
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    """
    Manages PostgreSQL connections for the CIROH AI Bot project.
    Supports both atomic queries and persistent sessions for batch operations.
    """
    def __init__(self):
        self._conn = None
        self.schema = os.getenv("POSTGRES_SCHEMA", "public")

    def _create_connection(self):
        """
        Establishes a physical connection and sets the search_path 
        to prioritize the version 2 schema.
        """
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        # Set the search path to ensure the V2 schema is prioritized over public (V1)
        with conn.cursor() as cur:
            cur.execute(f'SET search_path TO "{self.schema}", public;')
            conn.commit()
        return conn

    def __enter__(self):
        """
        Enables the use of 'with DatabaseManager() as db:' for session-based operations.
        Keeps a single connection open for the duration of the block.
        """
        self._conn = self._create_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Automatically closes the session connection upon exiting the 'with' block.
        """
        if self._conn:
            self._conn.close()
            self._conn = None

    def execute_query(self, query, params=None, fetch=False):
        """
        Executes a SQL query. 
        If a session connection exists, it uses it. 
        Otherwise, it creates and closes a temporary connection (atomic mode).
        """
        # Determine if we should use the existing session or a temporary connection
        is_temporary = self._conn is None
        conn = self._conn if not is_temporary else self._create_connection()
        
        try:
            # Using RealDictCursor for easier data handling (access by column name)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch:
                    return cur.fetchall()
                conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Database Error: {e}")
            return None
        finally:
            # Only close the connection if it was created specifically for this query
            if is_temporary:
                conn.close()

    def execute_batch(self, query, data_list, page_size=100):
        """
        Executes a high-performance batch insert using execute_values.
        Reduces network overhead and transaction commits.
        """
        is_temporary = self._conn is None
        conn = self._conn if not is_temporary else self._create_connection()
        
        try:
            with conn:
                with conn.cursor() as cur:
                    # execute_values is significantly faster than executing in a loop
                    execute_values(cur, query, data_list, page_size=page_size)
        except Exception as e:
            conn.rollback()
            print(f"Batch Database Error: {e}")
        finally:
            if is_temporary:
                conn.close()