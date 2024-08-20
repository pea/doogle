import RPi.GPIO as GPIO
import threading
import time

class RotaryEncoder:
    def __init__(self, button_callback, rotation_callback, long_press_callback=None, button_pin=17, clk_pin=18, dt_pin=19, long_press_duration=1):
        self.button_callback = button_callback
        self.rotation_callback = rotation_callback
        self.long_press_callback = long_press_callback
        self.long_press_duration = long_press_duration
        self.rotation_clicks = 0
        self.last_rotation_time = time.time()
        self.running = True
        self.button_press_time = None
        self.long_press_thread = None
        self.long_press_triggered = False

        self.button_pin = button_pin
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin

        # Set up GPIO pins
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        if self.button_pin is not None:
            GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(self.button_pin, GPIO.BOTH, callback=self.button_event)

        if self.clk_pin is not None and self.dt_pin is not None:
            GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.last_clk_state = GPIO.input(self.clk_pin)
            self.last_dt_state = GPIO.input(self.dt_pin)
            GPIO.add_event_detect(self.clk_pin, GPIO.BOTH, callback=self.rotate, bouncetime=2)

        # Start the timeout checker thread
        self.timeout_thread = threading.Thread(target=self.check_rotation_timeout)
        self.timeout_thread.start()

    def button_event(self, channel):
        if GPIO.input(self.button_pin) == GPIO.LOW:
            # Button pressed
            self.button_press_time = time.time()
            self.long_press_triggered = False
            if self.long_press_callback:
                self.long_press_thread = threading.Thread(target=self.check_long_press)
                self.long_press_thread.start()
        else:
            # Button released
            if self.long_press_thread:
                self.long_press_thread = None
            press_duration = time.time() - self.button_press_time
            if not self.long_press_triggered and press_duration < self.long_press_duration:
                self.button_callback()

    def check_long_press(self):
        while self.long_press_thread:
            if GPIO.input(self.button_pin) == GPIO.HIGH:
                # Button released before long press duration
                self.long_press_thread = None
                return
            if time.time() - self.button_press_time >= self.long_press_duration:
                self.long_press_callback()
                self.long_press_triggered = True
                self.long_press_thread = None
            time.sleep(0.1)

    def rotate(self, channel):
        clk_state = GPIO.input(self.clk_pin)
        dt_state = GPIO.input(self.dt_pin)

        if clk_state != self.last_clk_state:
            if dt_state != clk_state:
                self.rotation_clicks -= 1
            else:
                self.rotation_clicks += 1

            self.last_rotation_time = time.time()
            self.rotation_callback(self.rotation_clicks)

        self.last_clk_state = clk_state
        self.last_dt_state = dt_state

    def check_rotation_timeout(self):
        while self.running:
            if time.time() - self.last_rotation_time >= 5:
                self.rotation_clicks = 0
            time.sleep(0.1)

    def cleanup(self):
        self.running = False
        self.timeout_thread.join()
        GPIO.cleanup()