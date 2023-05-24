
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, QRadioButton, QPushButton
from PyQt5 import QtGui
import logging
import time

from pfm_config import *
from print_cmd import packet_outgoing_to_dict, packet_incoming_to_dict, cmd_dict_to_str

from hst_datalink import Datalink

# Logger
logger = logging.getLogger('Turret App')
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('{asctime} - {name:<34s} - {levelname:<7s} - {message}', style='{')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

################################################################################
##                             COMMMAND FUNCTIONS                             ##
################################################################################

# CMD_SET_TARGET_FREQ     
# CMD_SET_TARGET_DELTA    
# CMD_GET_DELTA_STEPS     
# CMD_GET_IMU_MEASUREMENT 
# CMD_SET_ISR_FREQ        
# CMD_ENABLE_CNC          
# CMD_DISABLE_CNC         
# CMD_SET_DELTA_STEPS     
# CMD_STOP                
# CMD_GET_ISR_FREQ     
   
   
class Turret_interface():
    def __init__(self, port, baudrate):
        self._datalink = None
        self._pfm_to_int={'x':1, 'y':2, 'z':4, 'a':8}
        
    def __del__(self):
        del self._datalink
       
    def _which_pfm_to_int(self, which_pfm:str):
        if which_pfm not in self._pfm_to_int.keys():
            raise ValueError(f"which_pfm={which_pfm} is not valid, valid values ['x', 'y', 'z', 'a'].")
        return self._pfm_to_int[which_pfm]
    
    def _check_integer(self, integer:int, bits:int, signed:bool, raise_error:bool=True):
        if bits not in [8, 16, 32]:
            raise ValueError(f"bits={bits} is not valid, valid values [8, 16, 32].")
        if signed:
            if bits==8:
                if -128 <= integer <= 127:
                    return True
            if bits==16:
                if -32768 <= integer <= 32767:
                    return True
            if bits==32:
                if -2147483648 <= integer <= 2147483647:
                    return True
        else:
            if bits==8:
                if 0 <= integer <= 255:
                    return True
            if bits==16:
                if 0 <= integer <= 65535:
                    return True
            if bits==32:
                if 0 <= integer <= 4294967296:
                    return True
        if raise_error:
            raise RuntimeError(f"integer={integer} (bits={bits}, signed={signed}) is outside of range.")
        return False

    def cmd_set_target_freq(self, which_pfm:str, freq:int, timeout_seconds:float=2.0,  wait_for_answer:bool=True):
        self._check_integer(integer=freq, bits=16, signed=False, raise_error=True)
        payload = bytearray([
                int.from_bytes(self._datalink.const.CMD_SET_TARGET_FREQ, byteorder=self._datalink.const.BYTEORDER), # command
                self._which_pfm_to_int(which_pfm), # payload: which pfm
                freq.to_bytes(2, byteorder=self._datalink.const.BYTEORDER)[0], # payload: freq lower
                freq.to_bytes(2, byteorder=self._datalink.const.BYTEORDER)[1], # payload: freq upper
            ])
        self._datalink.send(payload)
        if wait_for_answer:
            received, message = self._datalink.receive(since_time=time.time(), timeout_seconds=timeout_seconds, polling_period=0.001)
            if received:
                logger.info(f"answer ='{message}'")
                # return self._message_to_dict()
                return True
            else:
                logger.warning(f"answer = NO REPLY")
                return dict()
        else:
            logger.debug(f"answer = NOT REQUESTED")
            return dict()
        
    def cmd_set_target_delta(self, which_pfm:str, freq:int, delta:int, timeout_seconds:float=2.0, wait_for_answer:bool=True):
        self._check_integer(integer=freq, bits=16, signed=False, raise_error=True)
        self._check_integer(integer=delta, bits=32, signed=False, raise_error=True)
        payload = bytearray([
                int.from_bytes(self._datalink.const.CMD_SET_TARGET_DELTA, byteorder=self._datalink.const.BYTEORDER), # command
                self._which_pfm_to_int(which_pfm), # payload: which pfm
                freq.to_bytes(2, byteorder=self._datalink.const.BYTEORDER)[0], # payload: freq lower
                freq.to_bytes(2, byteorder=self._datalink.const.BYTEORDER)[1], # payload: freq upper
                freq.to_bytes(4, byteorder=self._datalink.const.BYTEORDER)[0], # payload: delta lower
                freq.to_bytes(4, byteorder=self._datalink.const.BYTEORDER)[1], # payload: delta  |
                freq.to_bytes(4, byteorder=self._datalink.const.BYTEORDER)[2], # payload: delta  |
                freq.to_bytes(4, byteorder=self._datalink.const.BYTEORDER)[3], # payload: delta upper
            ])
        self._datalink.send(payload)
        if wait_for_answer:
            received, message = self._datalink.receive(since_time=time.time(), timeout_seconds=timeout_seconds, polling_period=0.001)
            if received:
                logger.info(f"answer ='{message}'")
                return self._message_to_dict()
            else:
                logger.warning(f"answer = NO REPLY")
                return dict()
        else:
            logger.debug(f"answer = NOT REQUESTED")
            return dict()
        
        
    def cmd_get_delta_steps(self, which_pfm:str, timeout_seconds:float=2.0, wait_for_answer:bool=True):
        payload = bytearray([
                int.from_bytes(self._datalink.const.CMD_GET_DELTA_STEPS, byteorder=self._datalink.const.BYTEORDER), # command
                self._which_pfm_to_int(which_pfm), # payload: which pfm
            ])
        self._datalink.send(payload)
        if wait_for_answer:
            received, message = self._datalink.receive(since_time=time.time(), timeout_seconds=timeout_seconds, polling_period=0.001)
            if received:
                logger.info(f"answer ='{message}'")
                return self._message_to_dict()
            else:
                logger.warning(f"answer = NO REPLY")
                return dict()
        else:
            logger.debug(f"answer = NOT REQUESTED")
            return dict()
        
    
    def cmd_get_imu_measurement(self, timeout_seconds:float=2.0, wait_for_answer:bool=True):
        payload = bytearray([
                int.from_bytes(self._datalink.const.CMD_GET_IMU_MEASUREMENT, byteorder=self._datalink.const.BYTEORDER), # command
            ])
        self._datalink.send(payload)
        if wait_for_answer:
            received, message = self._datalink.receive(since_time=time.time(), timeout_seconds=timeout_seconds, polling_period=0.001)
            if received:
                logger.info(f"answer ='{message}'")
                return self._message_to_dict()
            else:
                logger.warning(f"answer = NO REPLY")
                return dict()
        else:
            logger.debug(f"answer = NOT REQUESTED")
            return dict()
        
        
    def cmd_set_isr_freq(self, isr_freq:int, timeout_seconds:float=2.0,  wait_for_answer:bool=True):
        self._check_integer(integer=isr_freq, bits=16, signed=False, raise_error=True)
        payload = bytearray([
                int.from_bytes(self._datalink.const.CMD_SET_ISR_FREQ, byteorder=self._datalink.const.BYTEORDER), # command
                isr_freq.to_bytes(2, byteorder=self._datalink.const.BYTEORDER)[0], # payload: freq lower
                isr_freq.to_bytes(2, byteorder=self._datalink.const.BYTEORDER)[1], # payload: freq upper
            ])
        self._datalink.send(payload)
        if wait_for_answer:
            received, message = self._datalink.receive(since_time=time.time(), timeout_seconds=timeout_seconds, polling_period=0.001)
            if received:
                logger.info(f"answer ='{message}'")
                # return self._message_to_dict()
                return True
            else:
                logger.warning(f"answer = NO REPLY")
                return dict()
        else:
            logger.debug(f"answer = NOT REQUESTED")
            return dict()        


    def cmd_enable_cnc(self, timeout_seconds:float=2.0,  wait_for_answer:bool=True):
        payload = bytearray([
                int.from_bytes(self._datalink.const.CMD_ENABLE_CNC, byteorder=self._datalink.const.BYTEORDER), # command
            ])
        self._datalink.send(payload)
        if wait_for_answer:
            received, message = self._datalink.receive(since_time=time.time(), timeout_seconds=timeout_seconds, polling_period=0.001)
            if received:
                logger.info(f"answer ='{message}'")
                # return self._message_to_dict()
                return True
            else:
                logger.warning(f"answer = NO REPLY")
                return dict()
        else:
            logger.debug(f"answer = NOT REQUESTED")
            return dict()  


    def cmd_disable_cnc(self, timeout_seconds:float=2.0,  wait_for_answer:bool=True):
        payload = bytearray([
                int.from_bytes(self._datalink.const.CMD_DISABLE_CNC, byteorder=self._datalink.const.BYTEORDER), # command
            ])
        self._datalink.send(payload)
        if wait_for_answer:
            received, message = self._datalink.receive(since_time=time.time(), timeout_seconds=timeout_seconds, polling_period=0.001)
            if received:
                logger.info(f"answer ='{message}'")
                # return self._message_to_dict()
                return True
            else:
                logger.warning(f"answer = NO REPLY")
                return dict()
        else:
            logger.debug(f"answer = NOT REQUESTED")
            return dict()  


    def cmd_set_delta_steps(self, which_pfm:str, delta_steps:int, timeout_seconds:float=2.0,  wait_for_answer:bool=True):
        self._check_integer(integer=delta_steps, bits=16, signed=False, raise_error=True)
        payload = bytearray([
                int.from_bytes(self._datalink.const.CMD_SET_DELTA_STEPS, byteorder=self._datalink.const.BYTEORDER), # command
                self._which_pfm_to_int(which_pfm), # payload: which pfm
                delta_steps.to_bytes(2, byteorder=self._datalink.const.BYTEORDER)[0], # payload: freq lower
                delta_steps.to_bytes(2, byteorder=self._datalink.const.BYTEORDER)[1], # payload: freq  |
                delta_steps.to_bytes(2, byteorder=self._datalink.const.BYTEORDER)[3], # payload: freq  |
                delta_steps.to_bytes(2, byteorder=self._datalink.const.BYTEORDER)[4], # payload: freq upper
            ])
        self._datalink.send(payload)
        if wait_for_answer:
            received, message = self._datalink.receive(since_time=time.time(), timeout_seconds=timeout_seconds, polling_period=0.001)
            if received:
                logger.info(f"answer ='{message}'")
                # return self._message_to_dict()
                return True
            else:
                logger.warning(f"answer = NO REPLY")
                return dict()
        else:
            logger.debug(f"answer = NOT REQUESTED")
            return dict()  


    def cmd_get_isr_freq(self, timeout_seconds:float=2.0, wait_for_answer:bool=True):
        payload = bytearray([
                int.from_bytes(self._datalink.const.CMD_GET_ISR_FREQ, byteorder=self._datalink.const.BYTEORDER), # command
            ])
        self._datalink.send(payload)
        if wait_for_answer:
            received, message = self._datalink.receive(since_time=time.time(), timeout_seconds=timeout_seconds, polling_period=0.001)
            if received:
                logger.info(f"answer ='{message}'")
                return self._message_to_dict()
            else:
                logger.warning(f"answer = NO REPLY")
                return dict()
        else:
            logger.debug(f"answer = NOT REQUESTED")
            return dict()


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
                                int.from_bytes(self.datalink.const.CMD_SET_TARGET_FREQ, byteorder=self.datalink.const.BYTEORDER), # coomand
                                255, # payload: which pfm
                                0, # payload: freq
                                7, # payload: freq
                                0, # payload: pfm direction
                                ],
                            )

        elif self.radio_btn_2.isChecked():
            message = bytearray([
                                int.from_bytes(self.datalink.const.CMD_SET_TARGET_FREQ, byteorder=self.datalink.const.BYTEORDER), # command
                                255, # payload: which pfm
                                0, # payload: freq
                                7, # payload: freq
                                255, # payload: pfm direction
                                ],
                            )
        elif self.radio_btn_3.isChecked():
            message = bytearray([
                                int.from_bytes(self.datalink.const.CMD_ENABLE_CNC, byteorder=self.datalink.const.BYTEORDER), # command
                                ],
                            )
        elif self.radio_btn_4.isChecked():
            message = bytearray([
                                int.from_bytes(self.datalink.const.CMD_DISABLE_CNC, byteorder=self.datalink.const.BYTEORDER), # command
                                ],
                            )
        elif self.radio_btn_5.isChecked():
            message = bytearray([
                                int.from_bytes(self.datalink.const.CMD_GET_IMU_MEASUREMENT, byteorder=self.datalink.const.BYTEORDER), # command
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
            logger.info(f"MainWindow.display_packet(): message: '{message}'")
            self.display_packet(message)
        else:
            logger.info(f"MainWindow.display_packet(): NO REPLY")

        
################################################################################
##                                    MAIN                                    ##
################################################################################
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec_())
