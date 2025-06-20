import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QProgressBar
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QFontDatabase, QPalette, QColor
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class GeckoTestbedUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_url = "http://localhost:5000"
        self.init_fonts()
        self.initUI()

    def init_fonts(self):
        font_db = QFontDatabase()
        exo2_path = "fonts/Exo2-VariableFont_wght.ttf"
        exo2_italic_path = "fonts/Exo2-Italic-VariableFont_wght.ttf"
        orbitron_path = "fonts/Orbitron-VariableFont_wght.ttf"
        if (font_db.addApplicationFont(exo2_path) != -1 and 
            font_db.addApplicationFont(exo2_italic_path) != -1 and 
            font_db.addApplicationFont(orbitron_path) != -1):
            logging.debug("Fonts loaded successfully")
        else:
            logging.warning("Failed to load fonts, using system defaults")

    def initUI(self):
        self.setWindowTitle("Gecko Testbed Control")
        self.setGeometry(100, 100, 1000, 600)  # Wider for axis controls
        self.setStyleSheet("""
            QMainWindow { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0A0A0A, stop:1 #1A237E); }
            QLabel { color: #FFFFFF; font-family: "Orbitron"; font-size: 14px; font-weight: 700; }
            QLineEdit { background: rgba(255, 255, 255, 0.1); border: 1px solid #00D4FF; color: #FFFFFF; padding: 5px; font-family: "Exo 2"; font-weight: 400; }
            QPushButton { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00D4FF, stop:1 #00FF7F); 
                border: 2px solid #00D4FF; 
                border-radius: 5px; 
                color: #0A0A0A; 
                padding: 10px; 
                font-family: "Orbitron"; 
                font-size: 14px; 
                font-weight: 700; 
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            QPushButton:pressed { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF4081, stop:1 #00FF7F); 
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); 
                padding-top: 12px; 
                padding-bottom: 8px;
            }
            QProgressBar { background: rgba(255, 255, 255, 0.1); border: 1px solid #00D4FF; color: #FFFFFF; }
            QProgressBar::chunk { background: #00D4FF; }
            QTableWidget { background: rgba(255, 255, 255, 0.1); color: #FFFFFF; border: 1px solid #00D4FF; font-family: "Exo 2"; font-weight: 400; }
        """)

        widget = QWidget()
        self.setCentralWidget(widget)
        main_layout = QHBoxLayout()
        widget.setLayout(main_layout)

        # Left Panel: Control & Automation
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        left_panel.setStyleSheet("background: rgba(255, 255, 255, 0.05); border-radius: 10px; padding: 10px;")

        # Control Section
        self.push_label = QLabel("Push Force (N):")
        self.push_input = QLineEdit("10")
        self.push_input.setAlignment(Qt.AlignRight)
        self.push_result = QLabel("Result: -- N")
        self.pull_label = QLabel("Pull Force (N):")
        self.pull_input = QLineEdit("50")
        self.pull_input.setAlignment(Qt.AlignRight)
        self.pull_result = QLabel("Result: -- N")
        self.push_button = QPushButton("Apply Push Force")
        self.pull_button = QPushButton("Apply Pull Force")

        # Automation Section
        self.auto_label = QLabel("Automation Steps:")
        self.auto_input = QLineEdit("100")
        self.auto_input.setAlignment(Qt.AlignRight)
        self.auto_button = QPushButton("Run Automation")
        self.progress = QProgressBar()
        self.progress.setValue(0)

        # Alignment Control Section
        self.align_label = QLabel("Alignment Control")
        self.x_label = QLabel("X Position (mm):")
        self.x_input = QLineEdit("0")
        self.x_input.setAlignment(Qt.AlignRight)
        self.x_button = QPushButton("Move X")
        self.y_label = QLabel("Y Position (mm):")
        self.y_input = QLineEdit("0")
        self.y_input.setAlignment(Qt.AlignRight)
        self.y_button = QPushButton("Move Y")
        self.z_label = QLabel("Z Position (mm):")
        self.z_input = QLineEdit("0")
        self.z_input.setAlignment(Qt.AlignRight)
        self.z_button = QPushButton("Move Z")
        self.reset_button = QPushButton("Reset Alignment")

        left_layout.addWidget(self.push_label)
        left_layout.addWidget(self.push_input)
        left_layout.addWidget(self.push_result)
        left_layout.addWidget(self.pull_label)
        left_layout.addWidget(self.pull_input)
        left_layout.addWidget(self.pull_result)
        left_layout.addWidget(self.push_button)
        left_layout.addWidget(self.pull_button)
        left_layout.addWidget(self.auto_label)
        left_layout.addWidget(self.auto_input)
        left_layout.addWidget(self.progress)
        left_layout.addWidget(self.auto_button)
        left_layout.addWidget(self.align_label)
        left_layout.addWidget(self.x_label)
        left_layout.addWidget(self.x_input)
        left_layout.addWidget(self.x_button)
        left_layout.addWidget(self.y_label)
        left_layout.addWidget(self.y_input)
        left_layout.addWidget(self.y_button)
        left_layout.addWidget(self.z_label)
        left_layout.addWidget(self.z_input)
        left_layout.addWidget(self.z_button)
        left_layout.addWidget(self.reset_button)
        left_layout.addStretch()

        # Right Panel: Data Visualization
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        right_panel.setStyleSheet("background: rgba(255, 255, 255, 0.05); border-radius: 10px; padding: 10px;")

        self.force_label = QLabel("Current Forces:")
        self.fx_label = QLabel("Fx: -- N")
        self.fy_label = QLabel("Fy: -- N")
        self.fz_label = QLabel("Fz: -- N")
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(5)
        self.data_table.setHorizontalHeaderLabels(["ID", "Fx (N)", "Fy (N)", "Fz (N)", "Timestamp"])

        right_layout.addWidget(self.force_label)
        right_layout.addWidget(self.fx_label)
        right_layout.addWidget(self.fy_label)
        right_layout.addWidget(self.fz_label)
        right_layout.addWidget(self.data_table)
        right_layout.addStretch()

        main_layout.addWidget(left_panel, 4)
        main_layout.addWidget(right_panel, 6)

        # Connect Buttons
        self.push_button.clicked.connect(self.apply_push)
        self.pull_button.clicked.connect(self.apply_pull)
        self.auto_button.clicked.connect(self.run_automation)
        self.x_button.clicked.connect(self.move_x)
        self.y_button.clicked.connect(self.move_y)
        self.z_button.clicked.connect(self.move_z)
        self.reset_button.clicked.connect(self.reset_alignment)

        # Timer for periodic data update
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)  # Update every 1 second

    def update_data(self):
        try:
            logging.debug(f"Fetching data from {self.api_url}/results")
            response = requests.get(f"{self.api_url}/results")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.data_table.setRowCount(len(data))
                    for i, row in enumerate(data):
                        self.data_table.setItem(i, 0, QTableWidgetItem(str(row.get('id', ''))))
                        self.data_table.setItem(i, 1, QTableWidgetItem(str(row.get('fx', ''))))
                        self.data_table.setItem(i, 2, QTableWidgetItem(str(row.get('fy', ''))))
                        self.data_table.setItem(i, 3, QTableWidgetItem(str(row.get('fz', ''))))
                        self.data_table.setItem(i, 4, QTableWidgetItem(str(row.get('timestamp', ''))))
                    logging.debug(f"Data updated successfully: {len(data)} rows")
                else:
                    logging.error(f"Unexpected data format: {data}")
                    self.push_result.setText("Error: Unexpected data format")
            else:
                logging.error(f"API returned status code: {response.status_code}, text: {response.text}")
                self.push_result.setText(f"Error: API request failed (Status: {response.status_code})")

            # Update live force readings
            force_response = requests.get(f"{self.api_url}/force")
            if force_response.status_code == 200:
                force_data = force_response.json()
                self.fx_label.setText(f"Fx: {force_data.get('Fx', '--')} N")
                self.fy_label.setText(f"Fy: {force_data.get('Fy', '--')} N")
                self.fz_label.setText(f"Fz: {force_data.get('Fz', '--')} N")
            else:
                logging.error(f"Force API error: {force_response.text}")
        except Exception as e:
            logging.error(f"Error updating data: {str(e)}")
            self.push_result.setText(f"Error: {str(e)}")

    def apply_push(self):
        try:
            logging.debug(f"Applying push force: {self.push_input.text()}")
            force = float(self.push_input.text())
            response = requests.post(f"{self.api_url}/apply_push", json={"force": force})
            if response.status_code == 200:
                data = response.json()
                if 'result' in data:
                    self.push_result.setText(f"Result: {data['result']:.2f} N")
                    logging.debug(f"Push force applied: {data['result']:.2f} N")
                elif 'error' in data:
                    self.push_result.setText(f"Error: {data['error']}")
                    logging.error(f"API error: {data['error']}")
                else:
                    self.push_result.setText("Error: Unknown response format")
                    logging.error("Unknown API response format")
            else:
                logging.error(f"API returned status code: {response.status_code}, text: {response.text}")
                self.push_result.setText(f"Error: API request failed (Status: {response.status_code})")
        except Exception as e:
            logging.error(f"Exception in apply_push: {str(e)}")
            self.push_result.setText(f"Error: {str(e)}")

    def apply_pull(self):
        try:
            logging.debug(f"Applying pull force: {self.pull_input.text()}")
            force = float(self.pull_input.text())
            response = requests.post(f"{self.api_url}/apply_pull", json={"force": force})
            if response.status_code == 200:
                data = response.json()
                if 'result' in data:
                    self.pull_result.setText(f"Result: {data['result']:.2f} N")
                    logging.debug(f"Pull force applied: {data['result']:.2f} N")
                elif 'error' in data:
                    self.push_result.setText(f"Error: {data['error']}")
                    logging.error(f"API error: {data['error']}")
                else:
                    self.push_result.setText("Error: Unknown response format")
                    logging.error("Unknown API response format")
            else:
                logging.error(f"API returned status code: {response.status_code}, text: {response.text}")
                self.pull_result.setText(f"Error: API request failed (Status: {response.status_code})")
        except Exception as e:
            logging.error(f"Exception in apply_pull: {str(e)}")
            self.pull_result.setText(f"Error: {str(e)}")

    def run_automation(self):
        try:
            logging.debug(f"Running automation with steps: {self.auto_input.text()}")
            steps = int(self.auto_input.text())
            self.progress.setMaximum(steps)
            response = requests.post(f"{self.api_url}/automate", json={"steps": steps, "push_force": 10, "pull_force": 50})
            if response.status_code == 200:
                data = response.json()
                if 'results' in data:
                    results = data['results']
                    self.progress.setValue(steps)
                    self.push_result.setText(f"Last Push: {results[-1]['push_result']:.2f} N")
                    self.pull_result.setText(f"Last Pull: {results[-1]['pull_result']:.2f} N")
                    logging.debug(f"Automation completed: {len(results)} steps")
                elif 'error' in data:
                    self.push_result.setText(f"Error: {data['error']}")
                    logging.error(f"API error: {data['error']}")
                else:
                    self.push_result.setText("Error: Unknown response format")
                    logging.error("Unknown API response format")
            else:
                logging.error(f"API returned status code: {response.status_code}, text: {response.text}")
                self.push_result.setText(f"Error: API request failed (Status: {response.status_code})")
        except Exception as e:
            logging.error(f"Exception in run_automation: {str(e)}")
            self.push_result.setText(f"Error: {str(e)}")

    def move_x(self):
        try:
            logging.debug(f"Moving X to: {self.x_input.text()}")
            position = float(self.x_input.text())
            if 0 <= position <= 100:  # Range limit
                response = requests.post(f"{self.api_url}/move/X", json={"position": position})
                if response.status_code == 200:
                    data = response.json()
                    if 'status' in data:
                        logging.debug(f"X moved to {position} mm")
                else:
                    logging.error(f"Move X failed: {response.text}")
            else:
                logging.error("X position out of range (0-100 mm)")
        except Exception as e:
            logging.error(f"Exception in move_x: {str(e)}")

    def move_y(self):
        try:
            logging.debug(f"Moving Y to: {self.y_input.text()}")
            position = float(self.y_input.text())
            if 0 <= position <= 50:  # Range limit
                response = requests.post(f"{self.api_url}/move/Y", json={"position": position})
                if response.status_code == 200:
                    data = response.json()
                    if 'status' in data:
                        logging.debug(f"Y moved to {position} mm")
                else:
                    logging.error(f"Move Y failed: {response.text}")
            else:
                logging.error("Y position out of range (0-50 mm)")
        except Exception as e:
            logging.error(f"Exception in move_y: {str(e)}")

    def move_z(self):
        try:
            logging.debug(f"Moving Z to: {self.z_input.text()}")
            position = float(self.z_input.text())
            if 0 <= position <= 30:  # Range limit
                response = requests.post(f"{self.api_url}/move/Z", json={"position": position})
                if response.status_code == 200:
                    data = response.json()
                    if 'status' in data:
                        logging.debug(f"Z moved to {position} mm")
                else:
                    logging.error(f"Move Z failed: {response.text}")
            else:
                logging.error("Z position out of range (0-30 mm)")
        except Exception as e:
            logging.error(f"Exception in move_z: {str(e)}")

    def reset_alignment(self):
        try:
            logging.debug("Resetting alignment to (0, 0, 0)")
            for axis in ['X', 'Y', 'Z']:
                response = requests.post(f"{self.api_url}/move/{axis}", json={"position": 0})
                if response.status_code != 200:
                    logging.error(f"Reset {axis} failed: {response.text}")
        except Exception as e:
            logging.error(f"Exception in reset_alignment: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GeckoTestbedUI()
    window.show()
    sys.exit(app.exec_())