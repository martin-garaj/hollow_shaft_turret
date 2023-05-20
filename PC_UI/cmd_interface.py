""" Naming convention

    Buffer: | ... | START_BYTES | PAYLOAD_SIZE | COMMAND | DATA | END_BYTES | ... | START_BYTES | ...|
    Packet:       | START_BYTES | PAYLOAD_SIZE | COMMAND | DATA | END_BYTES |
    Message:                    | PAYLOAD_SIZE | COMMAND | DATA |
    Payload:                                   | COMMAND | DATA |
    Data:                                                | DATA |

    Buffer
        - holds all incoming data (potentially consisting of multiple packets)
    Packet
        - holds structure representing single exchange of data (e.g. reply)
    Message
        - represents stripped-down version of packet without START_BYTES and END_BYTES
        - used only check_packet_complete()
    Payload
        - Message without PAYLOAD_SIZE
        - contains the Command and the Data
    Command
        - when transmitting, the Command is deciphered first, driving the state machine
        - when receiving, the Command is always repeated from the transmitted packet,
          since this is purely Master-Worker relation (Worker never initiates communication) 
    Data
        - Data carried by the packet (e.g. ACK, NACK, IMU data)
"""

import sys
import serial
from PyQt5.QtCore import QThread, QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, QRadioButton, QPushButton
from PyQt5 import QtGui
import logging
from datetime import datetime
from pfm_config import *
from print_cmd import packet_outgoing_to_dict, packet_incoming_to_dict, cmd_dict_to_str
import time
import collections 

from pkt_cmd_defs import *
from Packet import encode_packet, parse_buffer, parse_message

# Logger
logger = logging.getLogger('turret')
logger.setLevel(logging.DEBUG)
timestamp = datetime.now().strftime("%_Y_%m_%d__%H_%M_%S")
file_handler = logging.FileHandler(f"./logs/{timestamp}.log")
console_handler = logging.StreamHandler()
file_handler.setLevel(logging.DEBUG)
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)



class Receiver(QObject):
    """
    DOES: Runs in a separate thread, listening to incoming stream.

    :param QObject: _description_
    :type QObject: _type_
    :return: _description_
    :rtype: _type_
    """
    _interthread_signal = pyqtSignal(bytearray)
    def __init__(self, serial):
        super().__init__()
        # self._interthread_signal = pyqtSignal(bytearray)
        self._serial = serial
        self._buffer = bytearray()
        self.list_messages=collections.deque(maxlen=2)
        for i in range(2):
            self.list_messages.append({'time':time.time(), 'message':''})

    def run(self):
        """ Reads the incomming serial communication. 
        
        If responsible for detecting the packets and managing the buffer storing 
        raw incoming serial communication.
        
        """
        while True:
            if self._serial.inWaiting() > 0:
                # Read the data and append it to the raw_data buffer
                data = bytearray(self._serial.read(self._serial.in_waiting))
                self._buffer.extend(data)
                # Detect all packet present in the buffer
                packet_detected = True
                while packet_detected:
                    # Detect packet
                    self._buffer, message = parse_buffer(self._buffer)
                    print(f"{time.time()} Receiver.run(): message: '{message}'")
                    # Parse packet
                    if len(message) > 0:
                        packet_detected = True
                        self.list_messages.append({'time':time.time(), 'message':message})
                        print(f"{time.time()} Receiver.run(): self._interthread_signal.emit(message)")
                        # self._interthread_signal.emit(message)
                    else:
                        packet_detected = False
        
        
class DataLink():
    """
    DOES: Handles Packet level communication.
    DOESN'T: Examines the content of packets, except packet consistency.

    :param QObject: _description_
    :type QObject: _type_
    :return: _description_
    :rtype: _type_
    """     
    
    # _thread_receiver=None
    
    def __init__(self, port, baudrate):
        self._serial = serial.Serial(port, baudrate)
        self._receiver = Receiver(self._serial)
        # self.list_messages=collections.deque(maxlen=2)
        
        # for i in range(2):
            # self.list_messages.append({'time':time.time(), 'message':''})
        
        
        # more serial_receiver to separate thread
        self._thread_receiver = QThread()
        self._receiver.moveToThread(self._thread_receiver)
        self._thread_receiver.started.connect(self._receiver.run)
        self._receiver._interthread_signal.connect(self._update_list_messages)
        self._thread_receiver.start()
        
        
    def __del__(self):
        self._thread_receiver.stop()
        self._serial.disconnect()
        
    
    def _update_list_messages(self, message):
        """_summary_

        :param packet: _description_
        :type packet: _type_
        """
        receive_time = time.time()
        self.list_messages.append({
            "time":receive_time, 
            "message":message, 
        })
        print(f"{time.time()} DataLink._update_list_messages(): self.list_messages[-1]={self.list_messages[-1]}")


    def check_connection(self):
        return self._serial.is_open


    def send(self, message):
        # self._serial.write(message.encode())
        print(f"{time.time()} DataLink.send(): message: '{message}'")
        self._serial.write(message)
        
        
    def receive(self, since_time:float, timeout_seconds:float=1.0, polling_period:float=0.001):
        time_start = time.time()
        time_elapsed=0
        print(f"{time.time()} DataLink.receive(): since_time={since_time}")
        while time_elapsed < timeout_seconds:
            time_now = time.time()
            try:
                if self._receiver.list_messages[-1]['time'] > since_time:
                    return True, self._receiver.list_messages[-1]['message']
            except IndexError:
                pass
            
            time_elapsed = time_now - time_start
            time.sleep(polling_period)
        return False, None
    
################################################################################
##                                   WINDOW                                   ##
################################################################################
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.datalink = DataLink("/dev/ttyACM0", 115200)
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
        
        
    def display_packet(self, message):
        """ Maneges the display of Payload_content according to Command.
        
        :param dict_dislay: Dictionary containing parsed packet.
        :type dict_dislay: dict
        """

        command, data = parse_message(message)
        self.all_messages_edit.moveCursor(QtGui.QTextCursor.End)
        self.all_messages_edit.insertPlainText(f"{command}: {data}")
        text = self.all_messages_edit.toPlainText().split("\n")
        if len(text) > 5:
            self.all_messages_edit.setPlainText("\n".join(text[-5:]))

        self.radio_btn_2_messages_edit.moveCursor(QtGui.QTextCursor.End)
        pkt_string = cmd_dict_to_str(packet_incoming_to_dict(command, data))
        self.radio_btn_2_messages_edit.insertPlainText(f"{pkt_string}\n")
            
    def send_message(self):
        if self.radio_btn_1.isChecked():
            message = bytearray([
                                int.from_bytes(CMD_SET_TARGET_FREQ, byteorder=BYTEORDER), # coomand
                                255, # payload: which pfm
                                0, # payload: freq
                                7, # payload: freq
                                0, # payload: pfm direction
                                ],
                            )

        elif self.radio_btn_2.isChecked():
            message = bytearray([
                                int.from_bytes(CMD_SET_TARGET_FREQ, byteorder=BYTEORDER), # command
                                255, # payload: which pfm
                                0, # payload: freq
                                7, # payload: freq
                                255, # payload: pfm direction
                                ],
                            )
        elif self.radio_btn_3.isChecked():
            message = bytearray([
                                int.from_bytes(CMD_ENABLE_CNC, byteorder=BYTEORDER), # command
                                ],
                            )
        elif self.radio_btn_4.isChecked():
            message = bytearray([
                                int.from_bytes(CMD_DISABLE_CNC, byteorder=BYTEORDER), # command
                                ],
                            )
        elif self.radio_btn_5.isChecked():
            message = bytearray([
                                int.from_bytes(CMD_GET_IMU_MEASUREMENT, byteorder=BYTEORDER), # command
                                ],
                            )
        else:
            message = "No message selected"
            raise RuntimeError("This should not be reached.")
        self.radio_btn_1_messages_edit.moveCursor(QtGui.QTextCursor.End)
        tmp_packet_dict = packet_outgoing_to_dict(message[0], message[1:])
        pkt_string = cmd_dict_to_str(tmp_packet_dict)
        packet = encode_packet(message)
        self.radio_btn_1_messages_edit.insertPlainText(f"{pkt_string}\n")
            
        if isinstance(packet, str):
            packet = packet.encode()
            
        self.datalink.send(packet)    
        received, message = self.datalink.receive(since_time=time.time(), timeout_seconds=1.0, polling_period=0.01)
        if received:
            print(f"{time.time()} MainWindow.display_packet(): message: '{message}'")
            self.display_packet(message)
        else:
            print(f"{time.time()} MainWindow.send_message(): NO REPLY")

        
            
################################################################################
##                                    MAIN                                    ##
################################################################################
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec_())
