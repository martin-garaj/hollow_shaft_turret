""" Naming convention

    Buffer: | ... | START_BYTES | PAYLOAD_SIZE | COMMAND | PAYLOAD_CONTENT | END_BYTES | ... | START_BYTES | ...|
    Packet:       | START_BYTES | PAYLOAD_SIZE | COMMAND | PAYLOAD_CONTENT | END_BYTES |
    Message:                    | PAYLOAD_SIZE | COMMAND | PAYLOAD_CONTENT |
    Payload:                                   | COMMAND | PAYLOAD_CONTENT |
    Payload Content:                                     | PAYLOAD_CONTENT |

    Buffer
        - holds all incoming data (potentially consisting of multiple packets)
    Packet
        - holds structure data representing single exchange of data (e.g. reply)
    Message
        - Packet minus the START_BYTES, END_BYTES and Command
        - used only check_packet_complete()
    Payload
        - Packet minus the START_BYTES, END_BYTES and Payload size
        - contains the Command and the Payload content
    Payload Content
        - Content of the packet (e.g. ACK, NACK, IMU data)
"""

import sys
import serial
from PyQt5.QtCore import QThread, QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, QRadioButton, QPushButton
from PyQt5 import QtGui
import binascii

from pfm_config import *
from pkt_cmd_defs import *

# Message structure
START_BYTES = b'\xAA\xBB'
END_BYTES = b'\xCC\xDD'
BYTEORDER = 'little'
PAYLOAD_BYTE_SIZE = 1
COMMAND_BYTE_SIZE = 1


def encode_message(payload):
    """ Given a payload consisting of Command and Payload_content

    :param payload: _description_
    :type payload: _type_
    :return: _description_
    :rtype: _type_
    """
    # Payload size (2 bytes, little-endian)
    payload_size = len(payload)
    size_bytes = payload_size.to_bytes(PAYLOAD_BYTE_SIZE, byteorder=BYTEORDER)
    # Payload
    payload_bytes = bytes(payload)
    # Combine all bytes into a single message
    message = START_BYTES + size_bytes + payload_bytes + END_BYTES
    return message


def find_bytes(byte_array:bytearray, bytes:bytearray):
    """ Locate all indices of bytes-pattern within byte_array.

    :param byte_array: Array of bytes to be searched for a bytes-patter.
    :type byte_array: bytearray
    :param bytes: Patter of bytes to be searched for within byte_array.
    :type bytes: bytearray
    :return: List of indices, if no indices found returns [-1]
    :rtype: list
    """
    indices = []
    # print(f"find_bytes: len(bytes)={len(bytes)}")
    for i in range(len(byte_array)-1):
        if byte_array[i:i+len(bytes)] == bytes:
            indices.append(i)
            # print('appended')
    if len(indices) == 0:
        indices.append(-1)
    return indices


def bytearray_to_int(bytearray_int:bytearray, byteorder:str=BYTEORDER):
    """ Decode a bytearray into an integer.

    :param bytearray_int: Array of bytes encoding a single integer.
    :type bytearray_int: bytearray
    :param byteorder: Endianity, defaults to BYTEORDER
    :type byteorder: str, optional
    :return: Integer stored within the bytearray_int.
    :rtype: int
    """
    return int.from_bytes(bytearray_int, byteorder)


def check_packet_complete(expected_packet:bytearray):
    """ Check whether the packet is consistent according to message_size.

    :param buffer: _description_
    :type buffer: bytearray
    :param packet_start_idx: _description_
    :type packet_start_idx: int
    :param packet_end_idx: _description_
    :type packet_end_idx: int
    :return: _description_
    :rtype: _type_
    """
    payload_size_bytes = expected_packet[len(START_BYTES):len(START_BYTES)+PAYLOAD_BYTE_SIZE]
    message_size = bytearray_to_int(bytearray_int=payload_size_bytes) + PAYLOAD_BYTE_SIZE
    if message_size == len(expected_packet)-len(START_BYTES):
        packet = expected_packet[0:len(expected_packet)+len(END_BYTES)]
        return True, packet
    else:
        # false start and/or end of packet
        return False, bytearray()
        

def parse_buffer(buffer:bytearray):
    """ Searches for a first complete packet within the buffer.
    
    Function searches the first consistent packet between all valid 
    positions of START_BYTES and END_BYTES found in the buffer.
    Once the first consistent packet is found, updated buffer is returned 
    together with the content of the packet. If no packet is found, 
    an emptyarray representing the packet is returned.  
    
    Since only the first packet is returned, 
    this function can be called continuously.
    
    :param buffer: Array of all received data.
    :type buffer: bytearray
    :return: Returns (updated buffer, packet - empty if no packet is detected)
    :rtype: tuple(bytearray, bytearray)
    """
    # detect all START_BYTES
    packet_start_idxs = find_bytes(byte_array=buffer, bytes=START_BYTES)
    # print(packet_start_idxs)
    if packet_start_idxs[0] == -1:
        # no START_BYTES found, dump the buffer
        return bytearray(), bytearray()
    # detect all END_BYTES
    packet_end_idxs = find_bytes(byte_array=buffer, bytes=END_BYTES)
    # no END_BYTES found, return buffer to append more data
    if packet_end_idxs[0] == -1:
        return buffer, bytearray()
        
    # search for every start of the packet, until a packet of found
    for packet_start_idx in packet_start_idxs:
        for packet_end_idx in packet_end_idxs:
            expected_packet = buffer[packet_start_idx:packet_end_idx]
            #  packet_detected, packet = check_packet_complete(buffer=buffer, packet_start_idx=packet_start_idx, packet_end_idx=packet_end_idx)
            packet_detected, packet = check_packet_complete(expected_packet)
            if packet_detected:
                # remove the packet from the buffer
                buffer = buffer[packet_end_idx+len(END_BYTES):]
                return buffer, packet
            else:
                # continue the search
                pass
    return buffer, bytearray()


def parse_packet(packet:bytearray):
    """ Break the packet into Command and Payload_content

    :param packet: Complete packet, including START_BYTES and END_BYTES
    :type packet: bytearray
    :return: Returns (Command, Payload_content) 
    :rtype: tuple(bytearray, bytearray)
    """
    payload_size = bytearray_to_int( bytearray_int=packet[len(START_BYTES):len(START_BYTES)+PAYLOAD_BYTE_SIZE] )
    command = packet[len(START_BYTES)+PAYLOAD_BYTE_SIZE:len(START_BYTES)+PAYLOAD_BYTE_SIZE+COMMAND_BYTE_SIZE]
    payload_content_start = len(START_BYTES)+PAYLOAD_BYTE_SIZE+COMMAND_BYTE_SIZE
    payload_content = packet[payload_content_start:payload_content_start+payload_size-COMMAND_BYTE_SIZE]
    return command, payload_content

class SerialReader(QObject):
    data_ready = pyqtSignal(dict)

    def __init__(self, port, baudrate):
        super().__init__()
        self.serial = serial.Serial(port, baudrate)
        self.buffer_in = bytearray()

    def run(self):
        """ Reads the incomming serial communication. 
        
        If responsible for detecting the packets and managing the buffer storing 
        raw incoming serial communication.
        
        """
        while True:
            if self.serial.inWaiting() > 0:
                # Read the data and append it to the raw_data buffer
                data = bytearray(self.serial.read(self.serial.in_waiting))
                self.buffer_in.extend(data)
                
                # Detect all packet present in the buffer
                packet_detected = True
                while packet_detected:
                    # Detect packet
                    self.buffer_in, packet = parse_buffer(self.buffer_in)
                    # Parse packet
                    if len(packet) > 0:
                        packet_detected = True
                        command, payload_content = parse_packet(packet)
                        # self.display_packet(command, payload_content)
                        dict_dislay = {'command':command, 'payload_content':payload_content}
                        self.data_ready.emit(dict_dislay)
                        print(f"PACKET ({len(payload_content)}): CMD={command}, PYLD_CNTNT={payload_content}")
                    else:
                        packet_detected = False

    def write_serial(self, message):
        self.serial.write(message.encode())

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.serial_reader = SerialReader("/dev/ttyACM0", 115200)
        self.serial_thread = QThread()
        self.serial_reader.moveToThread(self.serial_thread)
        self.serial_thread.started.connect(self.serial_reader.run)
        self.serial_reader.data_ready.connect(self.display_packet)
        self.serial_thread.start()
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
        
    def display_packet(self, dict_dislay:dict):
        """ Maneges the display of Payload_content according to Command.
        
        :param dict_dislay: Dictionary containing parsed packet.
        :type dict_dislay: dict
        """
        command = dict_dislay['command']
        payload_content = dict_dislay['payload_content']
        self.all_messages_edit.moveCursor(QtGui.QTextCursor.End)
        self.all_messages_edit.insertPlainText(f"{command}: {payload_content}")
        text = self.all_messages_edit.toPlainText().split("\n")
        if len(text) > 5:
            self.all_messages_edit.setPlainText("\n".join(text[-5:]))

        # Parse the message and update the appropriate text edit box
        if command[0:COMMAND_BYTE_SIZE] == CMD_GET_IMU_MEASUREMENT:
            self.radio_btn_1_messages_edit.moveCursor(QtGui.QTextCursor.End)
            self.radio_btn_1_messages_edit.insertPlainText(f"{command}: {payload_content}")
        elif command[0:COMMAND_BYTE_SIZE] == CMD_ENABLE_CNC:
            self.radio_btn_2_messages_edit.moveCursor(QtGui.QTextCursor.End)
            self.radio_btn_2_messages_edit.insertPlainText(f"{command}: {payload_content}")


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
            print('DIR: False sent', flush=True)
            print(message, flush=True)
            message = encode_message(message)

        elif self.radio_btn_2.isChecked():
            message = bytearray([
                                int.from_bytes(CMD_SET_TARGET_FREQ, byteorder=BYTEORDER), # command
                                255, # payload: which pfm
                                0, # payload: freq
                                7, # payload: freq
                                255, # payload: pfm direction
                                ],
                            )
            print('DIR: True sent', flush=True)
            print(message, flush=True)
            message = encode_message(message)
        elif self.radio_btn_3.isChecked():
            message = bytearray([
                                int.from_bytes(CMD_ENABLE_CNC, byteorder=BYTEORDER), # command
                                ],
                            )
            print('ENABLE sent', flush=True)
            print(message, flush=True)
            message = encode_message(message)
        elif self.radio_btn_4.isChecked():
            message = bytearray([
                                int.from_bytes(CMD_DISABLE_CNC, byteorder=BYTEORDER), # command
                                ],
                            )
            message = encode_message(message)
            print('DISABLE sent', flush=True)
            print(message, flush=True)
        elif self.radio_btn_5.isChecked():
            message = bytearray([
                                int.from_bytes(CMD_GET_IMU_MEASUREMENT, byteorder=BYTEORDER), # command
                                ],
                            )
            print('Sending IMU message', flush=True)
            print(message, flush=True)
            message = encode_message(message)
        else:
            message = "No message selected"
            
        if isinstance(message, str):
            message = message.encode()
            
        self.serial_reader.serial.write(message)            
            

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec_())
