import sqlite3
import json
import sys

class Database:
  def __init__(self, db_name):
    self.db_name = db_name
    self.conn = sqlite3.connect(db_name, check_same_thread=False)
    self.create_tables() 

  def create_tables(self):
    queries = [
        '''
        CREATE TABLE IF NOT EXISTS activity (
          datetime TEXT,
          description TEXT
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS temperature (
          datetime TEXT,
          temperature REAL,
          fan_status TEXT
        )
        '''
    ]
    try:
        for query in queries:
            self.conn.execute(query)
        self.conn.commit()
    except Exception as e:
        print(f"Error creating tables: {e}", file=sys.stdout)

  def add_activity(self, datetime, description):
    query = '''
    INSERT INTO activity (datetime, description)
    VALUES (?, ?)
    '''
    try:
        self.conn.execute(query, (datetime, description))
        self.conn.commit()
    except Exception as e:
        print(f"Error adding item: {e}", file=sys.stdout)

  def add_temperature(self, datetime, temperature, fan_status):
    query = '''
    INSERT INTO temperature (datetime, temperature, fan_status)
    VALUES (?, ?, ?)
    '''
    try:
        self.conn.execute(query, (datetime, temperature, fan_status))
        self.conn.commit()
    except Exception as e:
        print(f"Error adding item: {e}", file=sys.stdout)

    self.limit_table_rows('temperature', 259200)

  def get_all_activity(self, page_size, page_number):
    query = '''
    SELECT * FROM activity
    ORDER BY datetime DESC
    LIMIT ? OFFSET ?
    '''
    try:
        offset = (page_number - 1) * page_size
        cursor = self.conn.execute(query, (page_size, offset))
        columns = [column[0] for column in cursor.description]
        items = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return json.dumps(items)
    except Exception as e:
        print(f"Error retrieving items: {e}", file=sys.stdout)

  def get_all_temperature(self, page_size, page_number):
    query = '''
    SELECT * FROM temperature
    ORDER BY datetime DESC
    LIMIT ? OFFSET ?
    '''
    try:
        offset = (page_number - 1) * page_size
        cursor = self.conn.execute(query, (page_size, offset))
        columns = [column[0] for column in cursor.description]
        items = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return json.dumps(items)
    except Exception as e:
        print(f"Error retrieving items: {e}", file=sys.stdout)

  def limit_table_rows(self, table_name, max_rows):
    query_count = f'SELECT COUNT(*) FROM {table_name}'
    cursor = self.conn.execute(query_count)
    count = cursor.fetchone()[0]

    if count > max_rows:
        query_delete_oldest = f'''
        DELETE FROM {table_name}
        WHERE datetime = (SELECT datetime FROM {table_name} ORDER BY datetime ASC LIMIT 1)
        '''
        try:
            self.conn.execute(query_delete_oldest)
            self.conn.commit()
        except Exception as e:
            print(f"Error deleting oldest item: {e}", file=sys.stdout)

  def close_connection(self):
    self.conn.close()