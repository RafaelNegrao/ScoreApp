import sqlite3
import logging
import re
from contextlib import contextmanager

class DBManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.table_whitelist = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
        self.column_whitelist = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

    def _validate_name(self, name, pattern):
        if not pattern.match(name):
            raise ValueError(f"Invalid name: {name}")

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _execute_with_retry(self, func, *args, **kwargs):
        max_retries = 5
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    self.logger.warning(f"Database locked, retrying... (attempt {attempt + 1})")
                    continue
                else:
                    self.logger.error(f"Database error: {e}")
                    raise

    def execute(self, query, params=None):
        def _execute():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                conn.commit()
                return cursor.lastrowid
        return self._execute_with_retry(_execute)

    def execute_many(self, query, params_list):
        def _execute_many():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount
        return self._execute_with_retry(_execute_many)

    def query(self, query, params=None):
        def _query():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        return self._execute_with_retry(_query)

    def query_one(self, query, params=None):
        def _query_one():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                row = cursor.fetchone()
                return dict(row) if row else None
        return self._execute_with_retry(_query_one)

    @contextmanager
    def transaction(self):
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Transaction rolled back: {e}")
            raise
        finally:
            conn.close()

    def load_list_options(self, table_name, id_column, name_column):
        self._validate_name(table_name, self.table_whitelist)
        self._validate_name(id_column, self.column_whitelist)
        self._validate_name(name_column, self.column_whitelist)
        query = f"SELECT {id_column}, {name_column} FROM {table_name} ORDER BY {name_column}"
        return self.query(query)