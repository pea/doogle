from flask import Flask, request
from flask_cors import CORS
from database import Database

try:
  from smbus2 import SMBus
  from bmp280 import BMP280
  is_temp_sensor_installed = True
except ImportError:
  is_temp_sensor_installed = False

class Api:
  def __init__(self):
    self.app = Flask(__name__)
    CORS(self.app)
    self.db = Database('activity.db')

    if is_temp_sensor_installed:
      self.bus = SMBus(1)
      self.bmp280 = BMP280(i2c_dev=self.bus)

    @self.app.route('/temperature', methods=['GET'])
    def get_temperature():
      page = request.args.get('page', default=1, type=int)
      response = self.db.get_all_temperature(1000, page)
      return response, 200, {'Content-Type': 'application/json'}
    
    @self.app.route('/activity', methods=['GET'])
    def get_activity():
      page = request.args.get('page', default=1, type=int)
      response = self.db.get_all_activity(100, page)
      return response, 200, {'Content-Type': 'application/json'}

  def start_server(self):
    self.app.run(host='0.0.0.0', port=5000)
