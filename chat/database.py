import sqlite3
import sys

class Database:
  def __init__(self, db_name):
    self.db_name = db_name
    self.conn = sqlite3.connect(db_name, check_same_thread=False)
    self.create_tables() 

  def create_tables(self):
    queries = [
        '''
        CREATE TABLE IF NOT EXISTS settings (
          muted BOOLEAN
        )
        '''
    ]
    try:
        for query in queries:
            self.conn.execute(query)
        self.conn.commit()
    except Exception as e:
        print(f"Error creating tables: {e}", file=sys.stdout)

  def update_muted(self, muted):
    query = '''
    UPDATE settings
    SET muted = ?
    '''
    self.conn.execute(query, (muted,))
    self.conn.commit()

  def get_muted(self):
    query = '''
    SELECT muted
    FROM settings
    '''
    cursor = self.conn.execute(query)
    muted = cursor.fetchone()
    if muted is not None:
        return muted[0]
    return None

  def close_connection(self):
    self.conn.close()