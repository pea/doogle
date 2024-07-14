from flask import Flask, request, send_file
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
    
    @self.app.route('/activity', methods=['GET'])
    def get_activity():
      page = request.args.get('page', default=1, type=int)
      per_page = request.args.get('per_page', default=100, type=int)
      response = self.db.get_all_activity(per_page, page)
      return response, 200, {'Content-Type': 'application/json'}
    
    @self.app.route('/videos', methods=['GET'])
    def get_videos():
      page = request.args.get('page', default=1, type=int)
      per_page = request.args.get('per_page', default=10, type=int)
      response = self.db.get_all_videos(per_page, page)
      return response, 200, {'Content-Type': 'application/json'}
    
    @self.app.route('/video', methods=['GET'])
    def get_video():
      filename = request.args.get('filename')
      file_path = f'videos/{filename}'
      return send_file(file_path, mimetype='video/mp4')
    
    @self.app.route('/system_info', methods=['GET'])
    def get_system_info():
      page = request.args.get('page', default=1, type=int)
      per_page = request.args.get('per_page', default=100, type=int)
      response = self.db.get_all_system_info(per_page, page)
      return response, 200, {'Content-Type': 'application/json'}
    
    @self.app.route('/ir_leds', methods=['POST'])
    def post_ir():
      data = request.get_json()
      if data.get('ir_behaviour') == 'on':
        self.db.update_setting('ir_led_behavior', 'on')
        return '', 200
      
      if data.get('ir_behaviour') == 'off':
        self.db.update_setting('ir_led_behavior', 'off')
        return '', 200

      if data.get('ir_behaviour') == 'auto':
        self.db.update_setting('ir_led_behavior', 'auto')
        return '', 200
        
      return '', 400
      
  def start_server(self):
    self.app.run(host='0.0.0.0', port=5000)
