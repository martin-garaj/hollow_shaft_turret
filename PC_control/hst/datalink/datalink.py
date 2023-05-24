

import serial
import time
from PyQt5.QtCore import QThread
from .receiver.receiver import Receiver
from ..packet.packet import encode_packet
import logging


class Datalink():
    """
    DOES: Handles Packet level communication.
    DOESN'T: Examines the content of packets, except packet consistency.

    :param QObject: _description_
    :type QObject: _type_
    :return: _description_
    :rtype: _type_
    """     
    
    def __init__(self, port, baudrate):
        self._logger = logging.getLogger(__name__)
        self._logger.info(f"DataLink.__init__(port={port}, baudrate={baudrate})")
        self._serial = serial.Serial(port, baudrate)
        self._receiver = Receiver(self._serial)
        
        # more serial_receiver to separate thread
        self._thread_receiver = QThread()
        self._receiver.moveToThread(self._thread_receiver)
        self._thread_receiver.started.connect(self._receiver.run)
        self._receiver._interthread_signal.connect(self._update_list_messages)
        self._thread_receiver.start()
        self._logger.info(f"DataLink.__init__()._thread_receiver.isRunning -> {self._thread_receiver.isRunning()}")
        
        
    def __del__(self):
        self._logger.info(f"DataLink.__del__()")
        if hasattr(self, '_thread_receiver'):
            self._thread_receiver.quit()
            del self._thread_receiver
            self._logger.debug(f"Receiver.__del__ -> del self._thread_receiver")
        if hasattr(self, '_serial'):
            self._serial.close()
            del self._serial
            self._logger.debug(f"Receiver.__del__ -> del self._serial")
        
    
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
        self._logger.debug(f"DataLink._update_list_messages() -> self.list_messages[-1]={self.list_messages[-1]}")


    def check_connection(self):
        self._logger.debug(f"DataLink.check_connection() -> self._serial.is_open={self._serial.is_open}")
        return self._serial.is_open


    def send(self, message):
        packet = encode_packet(message)
        self._logger.info(f"DataLink.send(message: '{message}') -> packet: '{packet}'")
        self._serial.write(packet)
        
        
    def receive(self, since_time:float, timeout_seconds:float=1.0, polling_period:float=0.001):
        time_start = time.time()
        time_elapsed=0
        while time_elapsed < timeout_seconds:
            time_now = time.time()
            try:
                if self._receiver.list_messages[-1]['time'] > since_time:
                    self._logger.debug(f"DataLink.receive(since_time={since_time}, timeout_seconds={timeout_seconds}, polling_period={polling_period})")
                    self._logger.info(f"DataLink.receive(...) -> True, '{self._receiver.list_messages[-1]['payload']}'")
                    payload = self._receiver.list_messages[-1]['payload']
                    return True, payload
            except IndexError:
                pass
            
            time_elapsed = time_now - time_start
            time.sleep(polling_period)
        self._logger.info(f"DataLink.receive(...) -> False, None")
        return False, None