from flask import Flask
from database import Database

class Api:
  def __init__(self):
    self.app = Flask(__name__)
    self.db = Database('activity.db')
    
    @self.app.route('/activity', methods=['GET'])
    def get_activity():
      response = self.db.get_all_items()
      return response, 200, {'Content-Type': 'application/json'}

  def start_server(self):
    self.app.run(host='0.0.0.0', port=5000)
