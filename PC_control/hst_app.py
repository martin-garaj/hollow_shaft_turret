
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, QRadioButton, QPushButton
from PyQt5 import QtGui
import logging
import time

from pfm_config import *
from print_cmd import packet_outgoing_to_dict, packet_incoming_to_dict, cmd_dict_to_str

from hst_datalink import Datalink

# Logger
# logger = logging.getLogger('turret')
# logger.setLevel(logging.DEBUG)
# timestamp = datetime.now().strftime("%_Y_%m_%d__%H_%M_%S")
# file_handler = logging.FileHandler(f"./logs/{timestamp}.log")
# console_handler = logging.StreamHandler()
# file_handler.setLevel(logging.DEBUG)
# console_handler.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# file_handler.setFormatter(formatter)
# console_handler.setFormatter(formatter)
# logger.addHandler(file_handler)
# logger.addHandler(console_handler)


################################################################################
##                                   WINDOW                                   ##
################################################################################
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.datalink = Datalink("/dev/ttyACM0", 115200)
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

        # command, data = Datalink.parse_message(message)
        command, data = message
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
                                int.from_bytes(Datalink.pkt.CMD_SET_TARGET_FREQ, byteorder=Datalink.pkt.BYTEORDER), # coomand
                                255, # payload: which pfm
                                0, # payload: freq
                                7, # payload: freq
                                0, # payload: pfm direction
                                ],
                            )

        elif self.radio_btn_2.isChecked():
            message = bytearray([
                                int.from_bytes(Datalink.pkt.CMD_SET_TARGET_FREQ, byteorder=Datalink.pkt.BYTEORDER), # command
                                255, # payload: which pfm
                                0, # payload: freq
                                7, # payload: freq
                                255, # payload: pfm direction
                                ],
                            )
        elif self.radio_btn_3.isChecked():
            message = bytearray([
                                int.from_bytes(Datalink.pkt.CMD_ENABLE_CNC, byteorder=Datalink.pkt.BYTEORDER), # command
                                ],
                            )
        elif self.radio_btn_4.isChecked():
            message = bytearray([
                                int.from_bytes(Datalink.pkt.CMD_DISABLE_CNC, byteorder=Datalink.pkt.BYTEORDER), # command
                                ],
                            )
        elif self.radio_btn_5.isChecked():
            message = bytearray([
                                int.from_bytes(Datalink.pkt.CMD_GET_IMU_MEASUREMENT, byteorder=Datalink.pkt.BYTEORDER), # command
                                ],
                            )
        else:
            message = "No message selected"
            raise RuntimeError("This should not be reached.")
        self.radio_btn_1_messages_edit.moveCursor(QtGui.QTextCursor.End)
        tmp_packet_dict = packet_outgoing_to_dict(message[0], message[1:])
        pkt_string = cmd_dict_to_str(tmp_packet_dict)
        self.radio_btn_1_messages_edit.insertPlainText(f"{pkt_string}\n")
        
        self.datalink.send(message)    
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
