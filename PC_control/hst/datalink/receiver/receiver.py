
import collections 
import time
from PyQt5.QtCore import QObject, pyqtSignal
from ...packet.packet import parse_buffer

import logging

class Receiver(QObject):
    """
    DOES: Runs in a separate thread, listening to incoming stream.

    :param QObject: _description_
    :type QObject: _type_
    :return: _description_
    :rtype: _type_
    """
    _interthread_signal = pyqtSignal(bytearray)
    _counter=0
    def __init__(self, serial):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._logger.info(f"Receiver.__init__(serial={serial.name})")
        self._serial = serial
        self._buffer = bytearray()
        self.list_messages=collections.deque(maxlen=2)
        for i in range(2):
            self.list_messages.append({'time':time.time(), 'message':''})
            

    def __del__(self):
        self._logger.info(f"Receiver.__del__()")

    def run(self):
        """ Reads the incomming serial communication. 
        
        If responsible for detecting the packets and managing the buffer storing 
        raw incoming serial communication.
        
        """
        self._logger.info(f"Receiver.run() executed")
        while True:
            if self._serial.inWaiting() > 0:
                # Read the data and append it to the raw_data buffer
                data = bytearray(self._serial.read(self._serial.in_waiting))
                self._buffer.extend(data)
                # Detect all packets present in the buffer
                packet_detected = True
                while packet_detected:
                    # Detect packet
                    self._buffer, payload = parse_buffer(self._buffer)
                    self._logger.debug(f"Receiver.run() payload: '{payload}'")
                    # Parse packet
                    if len(payload) > 0:
                        packet_detected = True
                        self.list_messages.append({'time':time.time(), 'payload':payload})
                        self._logger.debug(f"Receiver.run()->self.list_messages.append({self.list_messages[-1]})")
                    else:
                        packet_detected = False