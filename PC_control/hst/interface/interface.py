
import time
import logging
from ..datalink.datalink import Datalink
from ..packet.pkt_defs import *
from ..packet.packet import parse_message

class HST():
    """ API HST class
        This is an Application Programming Interface for Hollow Shaft Turret project.
        
        The API manages serial connection and communication with the embedded 
        platform controlling the turret mechanism.
        
        Public methods:
    
            hst()                       - constructor 
            cmd_set_target_freq()
            cmd_set_target_delta()
            cmd_get_delta_steps()
            cmd_get_imu_measurement()
            cmd_set_isr_freq()
            cmd_enable_cnc()
            cmd_disable_cnc()
            cmd_set_delta_steps()
            cmd_get_isr_freq()

    
    """
    def __init__(self, port:str, baudrate:int):
        """
        Initializes the HST API class with a specified port and baudrate.

        :param port: The port to be used for the serial connection.
        :type port: str
        :param baudrate: The baudrate for the serial connection.
        :type baudrate: int
        """
        self._logger = logging.getLogger(__name__)
        self._datalink = Datalink(port, baudrate)
        self._pfm_to_int={'x':PFM_X, 'y':PFM_Y, 'z':PFM_Z, 'a':PFM_A}
        
        
    def __del__(self):
        """
        Destructor for the HST API class, cleans up the datalink object.
        """
        del self._datalink
       
       
    def _which_pfm_to_int(self, which_pfm:str) -> int:
        """
        Converts a performance string to its corresponding integer value.

        :param which_pfm: The performance string to be converted.
        :type which_pfm: str
        :raises ValueError: If the input string is not a valid performance string.
        :return: The integer value corresponding to the input performance string.
        :rtype: int
        """
        if which_pfm not in self._pfm_to_int.keys():
            raise ValueError(f"which_pfm={which_pfm} is not valid, valid values ['x', 'y', 'z', 'a'].")
        return self._pfm_to_int[which_pfm]
    
    
    def _check_integer(self, integer:int, bits:int, signed:bool, raise_error:bool=True) -> bool:
        """
        Checks if an integer is within the valid range for a specified number of bits and sign.

        :param integer: The integer to be checked.
        :type integer: int
        :param bits: The number of bits that the integer should fit within.
        :type bits: int
        :param signed: Whether the integer is signed or not.
        :type signed: bool
        :param raise_error: Whether to raise an error if the integer is out of range, defaults to True.
        :type raise_error: bool, optional
        :raises ValueError: If the number of bits is not valid.
        :raises RuntimeError: If the integer is out of range and raise_error is True.
        :return: True if the integer is within range, False otherwise.
        :rtype: bool
        """
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


    def _payload_to_dict(self, command:int, data:bytearray) -> dict:
        """
        Converts a payload command and data into a dictionary.

        :param command: The command from the payload.
        :type command: int
        :param data: The data from the payload.
        :type data: bytearray
        :raises ValueError: If the command is not recognized.
        :return: A dictionary representation of the payload.
        :rtype: dict
        """
        info = dict()
        if command == CMD_SET_TARGET_FREQ:
            info['CMD'] = 'CMD_SET_TARGET_FREQ'
            info['ACK'] = True if int(data[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
        elif command == CMD_SET_TARGET_DELTA:
            info['CMD'] = 'CMD_SET_TARGET_DELTA'
            info['ACK'] = True if int(data[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
        elif command == CMD_GET_DELTA_STEPS:
            info['CMD'] = 'CMD_GET_DELTA_STEPS'
            if len(data) > 1:
                info['DELTA'] = int.from_bytes(data[0:4], byteorder=BYTEORDER)
            else:
                info['ACK'] = False if int(data[0])==int.from_bytes(PKT_NACK, byteorder=BYTEORDER) else 'ERROR'
        elif command == CMD_GET_IMU_MEASUREMENT:
            info['CMD'] = 'CMD_GET_IMU_MEASUREMENT'
            if len(data) > 1:
                for idx, value_type in enumerate(['AX', 'AY', 'AZ', 'GX', 'GY', 'GZ', 'MX', 'MY', 'MZ']):
                    val_start = idx*2
                    val_end = val_start+2
                    info[value_type] = int.from_bytes(data[val_start:val_end], byteorder=BYTEORDER)
            else:
                info['ACK'] = False if int(data[0])==int.from_bytes(PKT_NACK, byteorder=BYTEORDER) else 'ERROR'
        elif command == CMD_SET_ISR_FREQ:
            info['CMD'] = 'CMD_SET_ISR_FREQ'
            info['ACK'] = True if int(data[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
        elif command == CMD_ENABLE_CNC:
            info['CMD'] = 'CMD_ENABLE_CNC'
            info['ACK'] = True if int(data[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
        elif command == CMD_DISABLE_CNC:
            info['CMD'] = 'CMD_DISABLE_CNC'
            info['ACK'] = True if int(data[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
        elif command == CMD_SET_DELTA_STEPS:
            info['CMD'] = 'CMD_SET_DELTA_STEPS'
            info['ACK'] = True if int(data[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
        else:
            raise ValueError(f"command={command}, invalid value.")
        return info


    def _send_and_receive_message(self, payload:bytearray, since_time:float, wait_for_response:bool=True, timeout_seconds:float=2.0, polling_period:float=0.001) -> dict:
        """
        Sends a payload and waits for a response.

        :param payload: The payload to be sent.
        :type payload: bytearray
        :param since_time: The time since the payload was sent.
        :type since_time: float
        :param wait_for_response: Whether to wait for a response, defaults to True.
        :type wait_for_response: bool, optional
        :param timeout_seconds: The timeout period in seconds, defaults to 2.0.
        :type timeout_seconds: float, optional
        :param polling_period: The polling period in seconds, defaults to 0.001.
        :type polling_period: float, optional
        :return: A dictionary containing the response status and data.
        :rtype: dict
        """
        self._datalink.send(payload)
        if wait_for_response:
            received, payload = self._datalink.receive(since_time=since_time, timeout_seconds=timeout_seconds, polling_period=polling_period)
            if received:
                self._logger .info(f"_send_and_receive_message() -> payload='{payload}'")
                command, data = parse_message(payload)
                response = self._payload_to_dict(command, data)
                response['received'] = True
                return response
            else:
                self._logger .warning(f"_send_and_receive_message() -> TIMEOUT")
                return {'received':False}
        else:
            self._logger .info(f"_send_and_receive_message() -> response not requested")
            return {'received':False}


    def cmd_set_target_freq(self, which_pfm:str, freq:int, direction:bool, timeout_seconds:float=2.0,  wait_for_answer:bool=True, polling_period:float=0.001) -> dict:
        """
        Sends a command to set the target frequency.

        :param which_pfm: The pulse-frequency-modulator, valid values ['x', 'y', 'z', 'a'].
        :type which_pfm: str
        :param freq: The target frequency.
        :type freq: int
        :param direction: The direction of the frequency change.
        :type direction: bool
        :param timeout_seconds: The timeout period in seconds, defaults to 2.0.
        :type timeout_seconds: float, optional
        :param wait_for_answer: Whether to wait for a response, defaults to True.
        :type wait_for_answer: bool, optional
        :param polling_period: The polling period in seconds, defaults to 0.001.
        :type polling_period: float, optional
        :return: A dictionary containing the response status and data.
        :rtype: dict
        """
        self._check_integer(integer=freq, bits=16, signed=False, raise_error=True)
        payload = bytearray([
                int.from_bytes(CMD_SET_TARGET_FREQ, byteorder=BYTEORDER), # command
                self._which_pfm_to_int(which_pfm), # payload: which pfm
                freq.to_bytes(2, byteorder=BYTEORDER)[1], # payload: freq upper
                freq.to_bytes(2, byteorder=BYTEORDER)[0], # payload: freq lower
                direction.to_bytes(1, byteorder=BYTEORDER)[0], # payload: direction
            ])
        response = self._send_and_receive_message(payload=payload, since_time=time.time(), wait_for_response=wait_for_answer, timeout_seconds=timeout_seconds, polling_period=polling_period)
        return response
        
        
    def cmd_set_target_delta(self, which_pfm:str, freq:int, delta:int, timeout_seconds:float=2.0, wait_for_answer:bool=True, polling_period:float=0.001) -> dict:
        """
        Sends a command to set the target delta.

        :param which_pfm: The pulse-frequency-modulator, valid values ['x', 'y', 'z', 'a'].
        :type which_pfm: str
        :param freq: The target frequency.
        :type freq: int
        :param delta: The target delta.
        :type delta: int
        :param timeout_seconds: The timeout period in seconds, defaults to 2.0.
        :type timeout_seconds: float, optional
        :param wait_for_answer: Whether to wait for a response, defaults to True.
        :type wait_for_answer: bool, optional
        :param polling_period: The polling period in seconds, defaults to 0.001.
        :type polling_period: float, optional
        :return: A dictionary containing the response status and data.
        :rtype: dict
        """
        self._check_integer(integer=freq, bits=16, signed=False, raise_error=True)
        self._check_integer(integer=delta, bits=32, signed=False, raise_error=True)
        payload = bytearray([
                int.from_bytes(CMD_SET_TARGET_DELTA, byteorder=BYTEORDER), # command
                self._which_pfm_to_int(which_pfm), # payload: which pfm
                freq.to_bytes(2, byteorder=BYTEORDER)[1], # payload: freq upper
                freq.to_bytes(2, byteorder=BYTEORDER)[0], # payload: freq lower
                freq.to_bytes(4, byteorder=BYTEORDER)[3], # payload: delta upper
                freq.to_bytes(4, byteorder=BYTEORDER)[2], # payload: delta  |
                freq.to_bytes(4, byteorder=BYTEORDER)[1], # payload: delta  |
                freq.to_bytes(4, byteorder=BYTEORDER)[0], # payload: delta lower
            ])
        response = self._send_and_receive_message(payload=payload, since_time=time.time(), wait_for_response=wait_for_answer, timeout_seconds=timeout_seconds, polling_period=polling_period)
        return response
    
        
    def cmd_get_delta_steps(self, which_pfm:str, timeout_seconds:float=2.0, wait_for_answer:bool=True, polling_period:float=0.001) -> dict:
        """
        Sends a command to get the delta steps.

        :param which_pfm: The pulse-frequency-modulator, valid values ['x', 'y', 'z', 'a'].
        :type which_pfm: str
        :param timeout_seconds: The timeout period in seconds, defaults to 2.0.
        :type timeout_seconds: float, optional
        :param wait_for_answer: Whether to wait for a response, defaults to True.
        :type wait_for_answer: bool, optional
        :param polling_period: The polling period in seconds, defaults to 0.001.
        :type polling_period: float, optional
        :return: A dictionary containing the response status and data.
        :rtype: dict
        """
        payload = bytearray([
                int.from_bytes(CMD_GET_DELTA_STEPS, byteorder=BYTEORDER), # command
                self._which_pfm_to_int(which_pfm), # payload: which pfm
            ])
        response = self._send_and_receive_message(payload=payload, since_time=time.time(), wait_for_response=wait_for_answer, timeout_seconds=timeout_seconds, polling_period=polling_period)
        return response
    
    
    def cmd_get_imu_measurement(self, timeout_seconds:float=2.0, wait_for_answer:bool=True, polling_period:float=0.001) -> dict:
        """
        Get the Inertial Measurement Uunit measurement.

        :param timeout_seconds: The timeout period in seconds, defaults to 2.0.
        :type timeout_seconds: float, optional
        :param wait_for_answer: Whether to wait for a response, defaults to True.
        :type wait_for_answer: bool, optional
        :param polling_period: The polling period in seconds, defaults to 0.001.
        :type polling_period: float, optional
        :return: A dictionary containing the response status and data.
        :rtype: dict
        """
        payload = bytearray([
                int.from_bytes(CMD_GET_IMU_MEASUREMENT, byteorder=BYTEORDER), # command
            ])
        response = self._send_and_receive_message(payload=payload, since_time=time.time(), wait_for_response=wait_for_answer, timeout_seconds=timeout_seconds, polling_period=polling_period)
        return response
    
        
    def cmd_set_isr_freq(self, isr_freq:int, timeout_seconds:float=2.0,  wait_for_answer:bool=True, polling_period:float=0.001) -> dict:
        """
        Set the Iterrupt Service Routine frequency.

        :param isr_freq: The ISR frequency to be set.
        :type isr_freq: int
        :param timeout_seconds: The timeout period in seconds, defaults to 2.0.
        :type timeout_seconds: float, optional
        :param wait_for_answer: Whether to wait for a response, defaults to True.
        :type wait_for_answer: bool, optional
        :param polling_period: The polling period in seconds, defaults to 0.001.
        :type polling_period: float, optional
        :return: A dictionary containing the response status and data.
        :rtype: dict
        """
        self._check_integer(integer=isr_freq, bits=16, signed=False, raise_error=True)
        payload = bytearray([
                int.from_bytes(CMD_SET_ISR_FREQ, byteorder=BYTEORDER), # command
                isr_freq.to_bytes(2, byteorder=BYTEORDER)[1], # payload: freq upper
                isr_freq.to_bytes(2, byteorder=BYTEORDER)[0], # payload: freq lower
            ])
        response = self._send_and_receive_message(payload=payload, since_time=time.time(), wait_for_response=wait_for_answer, timeout_seconds=timeout_seconds, polling_period=polling_period)
        return response
    

    def cmd_enable_cnc(self, timeout_seconds:float=2.0,  wait_for_answer:bool=True, polling_period:float=0.001) -> dict:
        """
        Enable the Computerized Numerical Control module (includes all PFMs).

        :param timeout_seconds: The timeout period in seconds, defaults to 2.0.
        :type timeout_seconds: float, optional
        :param wait_for_answer: Whether to wait for a response, defaults to True.
        :type wait_for_answer: bool, optional
        :param polling_period: The polling period in seconds, defaults to 0.001.
        :type polling_period: float, optional
        :return: A dictionary containing the response status and data.
        :rtype: dict
        """
        payload = bytearray([
                int.from_bytes(CMD_ENABLE_CNC, byteorder=BYTEORDER), # command
            ])
        response = self._send_and_receive_message(payload=payload, since_time=time.time(), wait_for_response=wait_for_answer, timeout_seconds=timeout_seconds, polling_period=polling_period)
        return response
    

    def cmd_disable_cnc(self, timeout_seconds:float=2.0,  wait_for_answer:bool=True, polling_period:float=0.001) -> dict:
        """
        Disable the Computerized Numerical Control module (includes all PFMs).

        :param timeout_seconds: The timeout period in seconds, defaults to 2.0.
        :type timeout_seconds: float, optional
        :param wait_for_answer: Whether to wait for a response, defaults to True.
        :type wait_for_answer: bool, optional
        :param polling_period: The polling period in seconds, defaults to 0.001.
        :type polling_period: float, optional
        :return: A dictionary containing the response status and data.
        :rtype: dict
        """
        payload = bytearray([
                int.from_bytes(CMD_DISABLE_CNC, byteorder=BYTEORDER), # command
            ])
        response = self._send_and_receive_message(payload=payload, since_time=time.time(), wait_for_response=wait_for_answer, timeout_seconds=timeout_seconds, polling_period=polling_period)
        return response
    

    def cmd_set_delta_steps(self, which_pfm:str, delta_steps:int, timeout_seconds:float=2.0,  wait_for_answer:bool=True, polling_period:float=0.001) -> dict:
        """
        Sends a command to set the delta steps.

        :param which_pfm: The pulse-frequency-modulator, valid values ['x', 'y', 'z', 'a'].
        :type which_pfm: str
        :param delta_steps: The target delta steps.
        :type delta_steps: int
        :param timeout_seconds: The timeout period in seconds, defaults to 2.0.
        :type timeout_seconds: float, optional
        :param wait_for_answer: Whether to wait for a response, defaults to True.
        :type wait_for_answer: bool, optional
        :param polling_period: The polling period in seconds, defaults to 0.001.
        :type polling_period: float, optional
        :return: A dictionary containing the response status and data.
        :rtype: dict
        """
        self._check_integer(integer=delta_steps, bits=16, signed=False, raise_error=True)
        payload = bytearray([
                int.from_bytes(CMD_SET_DELTA_STEPS, byteorder=BYTEORDER), # command
                self._which_pfm_to_int(which_pfm), # payload: which pfm
                delta_steps.to_bytes(4, byteorder=BYTEORDER)[3], # payload: freq upper
                delta_steps.to_bytes(4, byteorder=BYTEORDER)[2], # payload: freq  |
                delta_steps.to_bytes(4, byteorder=BYTEORDER)[1], # payload: freq  |
                delta_steps.to_bytes(4, byteorder=BYTEORDER)[0], # payload: freq lower
            ])
        response = self._send_and_receive_message(payload=payload, since_time=time.time(), wait_for_response=wait_for_answer, timeout_seconds=timeout_seconds, polling_period=polling_period)
        return response
    

    def cmd_get_isr_freq(self, timeout_seconds:float=2.0, wait_for_answer:bool=True, polling_period:float=0.001) -> dict:
        """
        Get the Iterrupt Service Routine frequency.

        :param timeout_seconds: The timeout period in seconds, defaults to 2.0.
        :type timeout_seconds: float, optional
        :param wait_for_answer: Whether to wait for a response, defaults to True.
        :type wait_for_answer: bool, optional
        :param polling_period: The polling period in seconds, defaults to 0.001.
        :type polling_period: float, optional
        :return: A dictionary containing the response status and data.
        :rtype: dict
        """
        payload = bytearray([
                int.from_bytes(CMD_GET_ISR_FREQ, byteorder=BYTEORDER), # command
            ])
        response = self._send_and_receive_message(payload=payload, since_time=time.time(), wait_for_response=wait_for_answer, timeout_seconds=timeout_seconds, polling_period=polling_period)
        return response
