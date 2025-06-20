from flask import Flask, request, jsonify
import serial
import struct
import time
import sqlite3
import RPi.GPIO as GPIO
import logging
import threading
import glob

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# GPIO and Motor Setup
GPIO.setmode(GPIO.BCM)
AXES = {
    "X": (16, 26),  # Step, Dir pins
    "Y": (24, 25),
    "Z": (27, 17)
}
for step_pin, dir_pin in AXES.values():
    GPIO.setup(step_pin, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(dir_pin, GPIO.OUT, initial=GPIO.LOW)

step_delay = 0.001  # Adjustable step delay
moving = {ax: False for ax in AXES}
STEPS_PER_MM = 200  # Placeholder, calibrate based on motor resolution

# Sensor Setup
def find_serial_port():
    ports = glob.glob('/dev/tty[A-Za-z]*')
    for port in ports:
        if 'ttyUSB' in port or 'ttyACM' in port or 'ttyS0' in port:
            logging.debug(f"Found potential serial port: {port}")
            return port
    logging.error("No suitable serial port found")
    return '/dev/ttyUSB0'  # Default if none found

SERIAL_PORT = find_serial_port()
BAUDRATE = 115200
CALIBRATION_FACTORS = {'Fx': 20.0, 'Fy': 20.0, 'Fz': 20.0}  # Placeholder, calibrate
ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)

def raw_to_mv_v(raw, scale=2.0):
    return (raw - 32768) / 32768 * scale

def read_sensor():
    try:
        ser.write(b'\x23')
        time.sleep(0.1)
        ser.write(b'\x26\x01\x62\x65\x72\x6C\x69\x6E')
        time.sleep(0.1)
        ser.write(b'\x24')
        while True:
            frame = ser.read(11)
            if len(frame) == 11 and frame[0] == 0xA5:
                fx_raw = struct.unpack('>H', frame[1:3])[0]
                fy_raw = struct.unpack('>H', frame[3:5])[0]
                fz_raw = struct.unpack('>H', frame[5:7])[0]
                fx_mv_v = raw_to_mv_v(fx_raw)
                fy_mv_v = raw_to_mv_v(fy_raw)
                fz_mv_v = raw_to_mv_v(fz_raw)
                return {
                    'Fx': fx_mv_v * CALIBRATION_FACTORS['Fx'],
                    'Fy': fy_mv_v * CALIBRATION_FACTORS['Fy'],
                    'Fz': fz_mv_v * CALIBRATION_FACTORS['Fz']
                }
            time.sleep(0.05)
    except Exception as e:
        logging.error(f"Error reading sensor: {str(e)}")
        return {'Fx': 0.0, 'Fy': 0.0, 'Fz': 0.0}

class GeckoTestbed:
    def __init__(self):
        self.db_conn = sqlite3.connect("gecko_testbed.db", check_same_thread=False)
        self.create_db()
        self.sensor_thread = threading.Thread(target=self._sensor_loop, daemon=True)
        self.sensor_thread.start()

    def create_db(self):
        cursor = self.db_conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS test_results
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          fx REAL, fy REAL, fz REAL,
                          timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        self.db_conn.commit()

    def _sensor_loop(self):
        while True:
            force_data = read_sensor()
            self.store_result(force_data['Fx'], force_data['Fy'], force_data['Fz'])
            time.sleep(0.05)

    def store_result(self, fx, fy, fz):
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''INSERT INTO test_results (fx, fy, fz)
                             VALUES (?, ?, ?)''', (fx, fy, fz))
            self.db_conn.commit()
            logging.debug("Force data stored successfully")
        except Exception as e:
            logging.error(f"Error storing result: {str(e)}")

    def get_results(self):
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT id, fx, fy, fz, timestamp FROM test_results")
            results = [{"id": r[0], "fx": r[1], "fy": r[2], "fz": r[3], "timestamp": str(r[4])} for r in cursor.fetchall()]
            logging.debug(f"Retrieved {len(results)} results: {results}")
            return results
        except Exception as e:
            logging.error(f"Error fetching results: {str(e)}")
            return []

    def move_axis(self, axis, steps):
        if axis not in AXES:
            return False
        step_pin, dir_pin = AXES[axis]
        direction = steps >= 0
        steps = abs(steps)
        GPIO.output(dir_pin, GPIO.HIGH if direction else GPIO.LOW)
        for _ in range(steps):
            GPIO.output(step_pin, GPIO.HIGH)
            time.sleep(step_delay)
            GPIO.output(step_pin, GPIO.LOW)
            time.sleep(step_delay)
        return True

    def cleanup(self):
        GPIO.cleanup()
        self.db_conn.close()
        ser.close()

testbed = GeckoTestbed()

@app.route('/')
def index():
    return jsonify({"status": "API running"})

@app.route('/force', methods=['GET'])
def get_force():
    try:
        force_data = read_sensor()
        return jsonify(force_data)
    except Exception as e:
        logging.error(f"Error getting force: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route('/apply_push', methods=['POST'])
def apply_push():
    try:
        force = float(request.json.get('force', 0))
        force_data = read_sensor()
        return jsonify({"result": force_data['Fz']})
    except Exception as e:
        logging.error(f"Error in apply_push: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route('/apply_pull', methods=['POST'])
def apply_pull():
    try:
        force = float(request.json.get('force', 0))
        force_data = read_sensor()
        return jsonify({"result": -force_data['Fz']})
    except Exception as e:
        logging.error(f"Error in apply_pull: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route('/automate', methods=['POST'])
def automate():
    try:
        steps = int(request.json.get('steps', 0))
        push_force = float(request.json.get('push_force', 10))
        pull_force = float(request.json.get('pull_force', 50))
        results = []
        for _ in range(steps):
            force_data = read_sensor()
            results.append({"push_result": force_data['Fz'], "pull_result": -force_data['Fz']})
        return jsonify({"results": results})
    except Exception as e:
        logging.error(f"Error in automate: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route('/results', methods=['GET'])
def get_results():
    try:
        results = testbed.get_results()
        if not results:
            logging.warning("No results found in database")
            return jsonify([])
        return jsonify(results)
    except Exception as e:
        logging.error(f"Error in get_results: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route('/move/<axis>', methods=['POST'])
def move_axis(axis):
    try:
        axis = axis.upper()
        if axis not in AXES:
            return jsonify({"error": "Invalid axis"}), 400
        position = float(request.json.get('position', 0))  # mm
        steps = int(position * STEPS_PER_MM)  # Convert mm to steps
        success = testbed.move_axis(axis, steps)
        if success:
            return jsonify({"status": "Moved to position", "position": position})
        return jsonify({"error": "Movement failed"}), 400
    except Exception as e:
        logging.error(f"Error in move_{axis}: {str(e)}")
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        testbed.cleanup()