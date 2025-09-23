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
        self.log_table_name = 'log_table'
        self.current_user_wwid = None  # Armazenar WWID do usuário atual

    def set_current_user(self, wwid):
        """Define o WWID do usuário atual para ser usado nos logs"""
        self.current_user_wwid = wwid

    def _validate_name(self, name, pattern):
        if not pattern.match(name):
            raise ValueError(f"Invalid name: {name}")

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _log_db_change(self, conn, event, user=None, wwid=None):
        """Insert a record into the log table. conn must be an open sqlite3.Connection.

        Fields inserted: date (YYYY-MM-DD), time (HH:MM:SS), user, wwid, event
        This function is safe to call only when the underlying operation did not touch the log table
        (caller should avoid logging if the SQL touches `self.log_table_name`).
        """
        try:
            # Ensure WWID column exists
            self._ensure_wwid_column(conn)
            
            if user is None:
                try:
                    import getpass
                    user = getpass.getuser()
                except Exception:
                    user = 'unknown'

            if wwid is None:
                wwid = self.current_user_wwid or 'unknown'

            # Prepare fields
            from datetime import datetime
            now = datetime.now()
            date_str = now.strftime('%Y-%m-%d')
            time_str = now.strftime('%H:%M:%S')

            # Ensure event is a non-empty string; we may receive JSON strings or dicts
            if event is None:
                event = ''
            # If event is a dict or other structure, convert to JSON-like string
            if not isinstance(event, str):
                try:
                    import json
                    event = json.dumps(event, default=str)
                except Exception:
                    event = str(event)
            insert_sql = (
                f"INSERT INTO {self.log_table_name} (date, time, user, wwid, event) VALUES (?, ?, ?, ?, ?)"
            )
            cursor = conn.cursor()
            cursor.execute(insert_sql, (date_str, time_str, user, wwid, event))
        except Exception:
            # Never let logging break the calling operation; record to app logger instead
            self.logger.exception('Failed to write DB log entry')

    def _ensure_wwid_column(self, conn):
        """Ensure WWID column exists in the log table."""
        try:
            cursor = conn.cursor()
            # Check if WWID column exists
            cursor.execute(f'PRAGMA table_info({self.log_table_name})')
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'wwid' not in columns:
                self.logger.info("Adding WWID column to log table...")
                cursor.execute(f'ALTER TABLE {self.log_table_name} ADD COLUMN wwid TEXT')
                conn.commit()
                self.logger.info("WWID column added successfully")
        except Exception:
            self.logger.exception('Failed to ensure WWID column exists')

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

    def execute(self, query, params=None, skip_log=False):
        def _execute():
            # Avoid logging operations that touch the log table itself
            qtext = (query or '')
            should_log = self.log_table_name.lower() not in qtext.lower()
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Detect simple operation types and try to capture affected rows
                m_ins = re.match(r"\s*INSERT\s+INTO\s+([`\"]?)(?P<table>[A-Za-z_][A-Za-z0-9_]*)\1\s*\((?P<cols>[^)]*)\)\s*VALUES\s*\((?P<vals>.*)\)" , qtext, re.IGNORECASE)
                m_del = re.match(r"\s*DELETE\s+FROM\s+([`\"]?)(?P<table>[A-Za-z_][A-Za-z0-9_]*)\1(?:\s+WHERE\s+(?P<where>.*))?", qtext, re.IGNORECASE)
                m_upd = re.match(r"\s*UPDATE\s+([`\"]?)(?P<table>[A-Za-z_][A-Za-z0-9_]*)\1\s+SET\s+(?P<set>.+?)(?:\s+WHERE\s+(?P<where>.*))?$", qtext, re.IGNORECASE | re.DOTALL)

                before_rows = None
                op_tag = None
                payload = None

                try:
                    if m_del and should_log:
                        table = m_del.group('table')
                        where = m_del.group('where')
                        sel = f"SELECT * FROM {table}"
                        if where:
                            sel += f" WHERE {where}"
                        # Only attempt to capture deleted rows if WHERE clause doesn't contain placeholders
                        if where and '?' in where:
                            before_rows = None
                        else:
                            try:
                                cursor.execute(sel)
                                rows = cursor.fetchall()
                                before_rows = [dict(r) for r in rows]
                            except Exception:
                                before_rows = None
                        op_tag = '[EXCLUDED]'

                    elif m_upd and should_log:
                        table = m_upd.group('table')
                        where = m_upd.group('where')
                        sel = f"SELECT * FROM {table}"
                        if where:
                            sel += f" WHERE {where}"
                        # Only attempt to capture before state if WHERE clause doesn't contain placeholders
                        if where and '?' in where:
                            before_rows = None
                        else:
                            try:
                                cursor.execute(sel)
                                rows = cursor.fetchall()
                                before_rows = [dict(r) for r in rows]
                            except Exception:
                                before_rows = None
                        op_tag = '[UPDATED]'

                except Exception:
                    # don't block operation if inspection failed
                    self.logger.exception('Failed to inspect rows before operation')

                # Execute original query
                cursor.execute(query, params or ())
                lastrowid = cursor.lastrowid
                conn.commit()

                # After successful execution, prepare log payload for INSERT/UPDATE/DELETE when possible
                try:
                    if should_log and re.search(r"\b(insert|update|delete|replace)\b", qtext, re.IGNORECASE):
                        if m_ins:
                            op_tag = '[INCLUDED]'
                            # Try to parse column names and params to assemble inserted row(s)
                            cols = [c.strip().strip('`"') for c in m_ins.group('cols').split(',')]
                            # params may be used instead of inline values; attempt to use params when provided
                            if params:
                                # if params is a sequence, map to cols
                                try:
                                    insert_row = dict(zip(cols, params if isinstance(params, (list, tuple)) else [params]))
                                except Exception:
                                    insert_row = None
                            else:
                                # fallback: don't attempt to safely eval SQL values, skip payload
                                insert_row = None
                            payload = {'inserted': insert_row, 'lastrowid': lastrowid}

                        elif m_del:
                            op_tag = '[EXCLUDED]'
                            payload = {'deleted': before_rows}

                        elif m_upd:
                            # For UPDATE try to capture after state by selecting again
                            table = m_upd.group('table')
                            where = m_upd.group('where')
                            set_clause = m_upd.group('set')
                            after_rows = None
                            where_params = None
                            if where:
                                # Extract params for WHERE clause
                                num_set_params = set_clause.count('?')
                                if params and len(params) > num_set_params:
                                    where_params = params[num_set_params:]
                            
                            try:
                                sel = f"SELECT * FROM {table}"
                                if where:
                                    sel += f" WHERE {where}"
                                cursor.execute(sel, where_params or ())
                                rows = cursor.fetchall()
                                after_rows = [dict(r) for r in rows]
                            except Exception as e:
                                self.logger.warning(f"Could not capture after_rows for UPDATE: {e}")
                                after_rows = None
                            op_tag = '[UPDATED]'
                            payload = {'before': before_rows, 'after': after_rows}

                        # Build event as JSON string with tag prefix
                        import json
                        if op_tag is None:
                            op_tag = '[INFO]'
                        if payload is None:
                            payload = {}
                        event_text = f"{op_tag} " + json.dumps(payload, default=str)
                        try:
                            if not skip_log:
                                self._log_db_change(conn, event=event_text)
                            conn.commit()
                        except Exception:
                            pass
                except Exception:
                    self.logger.exception('Failed to create DB log entry')

                return lastrowid
        return self._execute_with_retry(_execute)

    def execute_many(self, query, params_list, skip_log=False):
        def _execute_many():
            qtext = (query or '')
            should_log = self.log_table_name.lower() not in qtext.lower()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                rowcount = cursor.rowcount
                conn.commit()
                try:
                    if should_log and re.search(r"\b(insert|update|delete|replace)\b", qtext, re.IGNORECASE):
                        # For executemany we log a summary only
                        import json
                        event_text = '[INCLUDED]' if re.search(r"\binsert\b", qtext, re.IGNORECASE) else '[UPDATED/EXCLUDED]'
                        payload = {'rows': rowcount}
                        event_text = event_text + ' ' + json.dumps(payload)
                        try:
                            if not skip_log:
                                self._log_db_change(conn, event=event_text)
                            conn.commit()
                        except Exception:
                            pass
                except Exception:
                    self.logger.exception('Failed to create DB log entry for executemany')
                return rowcount
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
    def transaction(self, event: str = None, user: str = None, wwid: str = None):
        """Context manager for transactions.

        Optional `event`, `user`, and `wwid` can be provided to write a single log entry after successful commit.
        Example:
            with db.transaction(event='Updated supplier X', user='John', wwid='AN123') as conn:
                conn.execute(...)  # normal sqlite3 API
        """
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
            # only log if event provided and the transaction did not touch the log table
            if event:
                # We can't easily inspect the executed SQL statements on this connection,
                # so as a best-effort avoid logging if the connection had operations on the log_table name present
                # in the connection's trace or similar isn't available; instead we assume caller won't log events
                # for operations that themselves write to the log table.
                try:
                    self._log_db_change(conn, event=event, user=user, wwid=wwid)
                    conn.commit()
                except Exception:
                    pass
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