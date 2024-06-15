import sqlite3
import json
import sys

class Database:
  def __init__(self, db_name):
    self.db_name = db_name
    self.conn = sqlite3.connect(db_name, check_same_thread=False)
    self.create_table()

  def create_table(self):
    query = '''
    CREATE TABLE IF NOT EXISTS activity (
      datetime TEXT,
      description TEXT
    )
    '''
    try:
        self.conn.execute(query)
        self.conn.commit()
    except Exception as e:
        print(f"Error creating table: {e}", file=sys.stdout)

  def add_item(self, datetime, description):
    query = '''
    INSERT INTO activity (datetime, description)
    VALUES (?, ?)
    '''
    try:
        self.conn.execute(query, (datetime, description))
        self.conn.commit()
    except Exception as e:
        print(f"Error adding item: {e}", file=sys.stdout)

  def get_all_items(self):
    query = '''
    SELECT * FROM activity
    '''
    try:
        cursor = self.conn.execute(query)
        columns = [column[0] for column in cursor.description]
        items = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return json.dumps(items)
    except Exception as e:
        print(f"Error retrieving items: {e}", file=sys.stdout)

  def close_connection(self):
    self.conn.close()