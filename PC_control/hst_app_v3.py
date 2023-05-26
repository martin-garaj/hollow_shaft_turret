
import sys
import logging
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, QRadioButton, QPushButton
from PyQt5 import QtGui
from hst.interface import HST


# Logger
logger = logging.getLogger('Turret App')
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('{asctime} - {name:<34s} - {levelname:<7s} - {message}', style='{')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


################################################################################
##                                   WINDOW                                   ##
################################################################################
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.turret = HST("/dev/ttyACM0", 115200)
        # self.datalink = Datalink("/dev/ttyACM0", 115200)
        self.init_ui()

    def init_ui(self):
        self.setGeometry(100, 100, 600, 400)
        self.setWindowTitle('Serial Reader')

        # Create radio buttons
        self.radio_btn_1 = QRadioButton("DIR: False")
        self.radio_btn_2 = QRadioButton("DIR: True")
        self.radio_btn_3 = QRadioButton("ENABLE")
        self.radio_btn_4 = QRadioButton("DISABLE")
        self.radio_btn_5 = QRadioButton("IMU reading")

        # Create send button
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)

        # Create layout for radio buttons and send button
        hbox = QHBoxLayout()
        hbox.addWidget(self.radio_btn_1)
        hbox.addWidget(self.radio_btn_2)
        hbox.addWidget(self.radio_btn_3)
        hbox.addWidget(self.radio_btn_4)
        hbox.addWidget(self.radio_btn_5)
        hbox.addWidget(self.send_btn)

        # Create layout for text edit boxes
        vbox = QVBoxLayout()
        self.all_messages_edit = QTextEdit(self)
        self.radio_btn_1_messages_edit = QTextEdit(self)
        self.radio_btn_2_messages_edit = QTextEdit(self)

        # Add text edit boxes to the main layout
        vbox.addWidget(self.all_messages_edit)
        vbox.addWidget(self.radio_btn_1_messages_edit)
        vbox.addWidget(self.radio_btn_2_messages_edit)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.show()
        
            
    def send_message(self):
        if self.radio_btn_1.isChecked():
            response = self.turret.cmd_set_target_freq(which_pfm='x', freq=7, direction=True, timeout_seconds=2.0,  wait_for_answer=True)
        elif self.radio_btn_2.isChecked():
            response = self.turret.cmd_set_target_freq(which_pfm='x', freq=7, direction=False, timeout_seconds=2.0,  wait_for_answer=True)
        elif self.radio_btn_3.isChecked():
            response = self.turret.cmd_enable_cnc(timeout_seconds=2.0,  wait_for_answer=True)
        elif self.radio_btn_4.isChecked():
            response = self.turret.cmd_disable_cnc(timeout_seconds=2.0,  wait_for_answer=True)
        elif self.radio_btn_5.isChecked():
            response = self.turret.cmd_get_imu_measurement(timeout_seconds=2.0,  wait_for_answer=True)
        else:
            raise RuntimeError("This should not be reached.")
        self.radio_btn_1_messages_edit.moveCursor(QtGui.QTextCursor.End)
        if response['received']:
            logger.info(f"MainWindow.display_packet(): message: '{response}'")
            self.radio_btn_2_messages_edit.moveCursor(QtGui.QTextCursor.End)
            self.radio_btn_2_messages_edit.insertPlainText(f"{response}\n")
        else:
            logger.info(f"MainWindow.display_packet(): NO REPLY")

################################################################################
##                                    MAIN                                    ##
################################################################################
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec_())
