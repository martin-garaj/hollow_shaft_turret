
import serial
import time
from PyQt5.QtCore import QThread
from .receiver.receiver import Receiver
from ..packet.packet import encode_packet
import logging


class Datalink():
    """
    Datalink class handles packet-level communication. For packet definition 
    and terminology refer to packet.packet.
    """     
    
    def __init__(self, port, baudrate):
        """
        Initializes the Datalink object.

        :param port: The port to be used for the serial connection.
        :type port: str
        :param baudrate: The baudrate to be used for the serial connection.
        :type baudrate: int
        """
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
        """
        Deletes the Datalink object, closing the serial connection and 
        stopping the receiver thread.
        """
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
        """
        Updates the list of messages with the received message.

        :param message: The received message.
        :type message: str
        """
        receive_time = time.time()
        self.list_messages.append({
            "time":receive_time, 
            "message":message, 
        })
        self._logger.debug(f"DataLink._update_list_messages() -> self.list_messages[-1]={self.list_messages[-1]}")


    def check_connection(self):
        """
        Checks the status of the serial connection.

        :return: True if the serial connection is open, False otherwise.
        :rtype: bool
        """
        self._logger.debug(f"DataLink.check_connection() -> self._serial.is_open={self._serial.is_open}")
        return self._serial.is_open


    def send(self, message):
        """
        Sends a message over the serial connection.

        :param message: The message to be sent.
        :type message: str
        """
        packet = encode_packet(message)
        self._logger.info(f"DataLink.send(message: '{message}') -> packet: '{packet}'")
        self._serial.write(packet)
        
        
    def receive(self, since_time:float, timeout_seconds:float=1.0, polling_period:float=0.001):
        """
        Receives a message over the serial connection.

        :param since_time: The time since the received message is considered as new.
        :type since_time: float
        :param timeout_seconds: The timeout period in seconds, defaults to 1.0.
        :type timeout_seconds: float, optional
        :param polling_period: The polling period in seconds, defaults to 0.001.
        :type polling_period: float, optional
        :return: A tuple containing a boolean indicating whether a message was received and the received message.
        :rtype: tuple
        """
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