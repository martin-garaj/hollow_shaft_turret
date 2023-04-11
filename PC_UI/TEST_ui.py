import sys
import serial
from PyQt5.QtCore import QThread, QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, QRadioButton, QPushButton
from PyQt5 import QtGui

from pfm_config import *
from pkt_cmd_defs import *

BYTEORDER = 'little'


import struct

# Message structure
START_BYTES = b'\xAA\xBB'
END_BYTES = b'\xCC\xDD'


def encode_message(payload):
    # Payload size (2 bytes, little-endian)
    payload_size = len(payload)
    size_bytes = payload_size.to_bytes(1, byteorder=BYTEORDER)
    # Payload
    payload_bytes = bytes(payload)
    # Combine all bytes into a single message
    message = START_BYTES + size_bytes + payload_bytes + END_BYTES
    return message


def decode_message(data):
    # Find the start bytes
    start_index = data.find(START_BYTES)
    if start_index == -1:
        # Start bytes not found, invalid message
        return None, data
    # Find the ending bytes
    end_index = data.find(END_BYTES, start_index)
    if end_index == -1:
        # Ending bytes not found, incomplete message
        return None, data[start_index:]
    # Extract the payload size
    size_bytes = data[start_index+2:start_index+3]
    payload_size = int.from_bytes(size_bytes, byteorder=BYTEORDER)
    # Extract the payload
    payload = data[start_index+3:start_index+3+payload_size]
    # Remove the message from the data buffer
    remaining_data = data[start_index+3+payload_size:]
    return payload, remaining_data







class SerialReader(QObject):
    data_ready = pyqtSignal(str)

    def __init__(self, port, baudrate):
        super().__init__()
        self.serial = serial.Serial(port, baudrate)

    def run(self):
        while True:
            if self.serial.inWaiting() > 0:
                data = self.serial.read(self.serial.in_waiting).decode('utf-8', errors='backslashreplace')
                self.data_ready.emit(data)
            # if self.serial.inWaiting() > 0:
            #     # data = self.serial.read(self.serial.in_waiting).decode('utf-8', errors='backslashreplace')
            #     data += str(self.serial.read(self.serial.in_waiting).decode('utf-8', errors='backslashreplace'))
                
            #     # print(type(data))
            #     console_oupput, _ = decode_message(data)
            #     if not isinstance(console_oupput, type(None)):
            #         self.data_ready.emit(console_oupput)
            #         # self.data_ready.emit(console_oupput)
            #     else:
            #         self.data_ready.emit(data)
                
    def write_serial(self, message):
        self.serial.write(message.encode())

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.serial_reader = SerialReader("/dev/ttyACM0", 115200)
        self.serial_thread = QThread()
        self.serial_reader.moveToThread(self.serial_thread)
        self.serial_thread.started.connect(self.serial_reader.run)
        self.serial_reader.data_ready.connect(self.update_text_edit)
        self.serial_thread.start()
        self.init_ui()

    def init_ui(self):
        self.setGeometry(100, 100, 400, 400)
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

        # Create layout for text edit box
        vbox = QVBoxLayout()
        self.text_edit = QTextEdit(self)
        vbox.addWidget(self.text_edit)
        
        # Add radio button and text edit box layouts to main layout
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.show()

    def update_text_edit(self, data):
        self.text_edit.moveCursor(QtGui.QTextCursor.End)
        self.text_edit.insertPlainText(data)
        text = self.text_edit.toPlainText().split("\n")
        if len(text) > 5:
            self.text_edit.setPlainText("\n".join(text[-5:]))

    def send_message(self):
        if self.radio_btn_1.isChecked():
            speed = 1
            message = bytearray([
                                int.from_bytes(CMD_SET_TARGET_FREQ, byteorder=BYTEORDER), # coomand
                                255, # payload: which pfm
                                0, # payload: freq
                                7, # payload: freq
                                0, # payload: pfm direction
                                ],
                            )
            message = encode_message(message)
            print(message)
            
        elif self.radio_btn_2.isChecked():
            message = bytearray([
                                int.from_bytes(CMD_SET_TARGET_FREQ, byteorder=BYTEORDER), # command
                                255, # payload: which pfm
                                0, # payload: freq
                                7, # payload: freq
                                255, # payload: pfm direction
                                ],
                            )
            message = encode_message(message)
            print(message)
        elif self.radio_btn_3.isChecked():
            message = bytearray([
                                int.from_bytes(CMD_ENABLE_CNC, byteorder=BYTEORDER), # command
                                ],
                            )
            message = encode_message(message)
            print(message)
        elif self.radio_btn_4.isChecked():
            message = bytearray([
                                int.from_bytes(CMD_DISABLE_CNC, byteorder=BYTEORDER), # command
                                ],
                            )
            message = encode_message(message)
            print(message)
        elif self.radio_btn_5.isChecked():
            message = bytearray([
                                int.from_bytes(CMD_GET_IMU_MEASUREMENT, byteorder=BYTEORDER), # command
                                ],
                            )
            message = encode_message(message)
            print(message)
        else:
            message = "No message selected"
            
        if isinstance(message, str):
            message = message.encode()
            
        self.serial_reader.serial.write(message)            
            

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec_())
