""" This file documents the command structure by parsing the commands in their
byt format into a structured and human-readable format.

The command functions in their original form can be found in pkt_process_cmd.cpp
and the command constants are defined in pkt_cmd_defs.h

"""

from pkt_cmd_defs import *
from pkt_ack_defs import *
import serial
from PyQt5.QtCore import QThread, QObject, pyqtSignal
import time
PAYLOAD_BYTE_SIZE = 1
COMMAND_BYTE_SIZE = 1

################################################################################
##                                SerialReader                                ##
################################################################################
# class SerialReader(QObject):
#     data_ready = pyqtSignal(dict)

#     def __init__(self, port, baudrate):
#         super().__init__()
#         self.serial = serial.Serial(port, baudrate)
#         self.buffer_in = bytearray()

#     def __del__(self):
#         self.serial.close()

#     def run(self):
#         """ Reads the incomming serial communication. 
        
#         If responsible for detecting the packets and managing the buffer storing 
#         raw incoming serial communication.
        
#         """
#         while True:
#             if self.serial.inWaiting() > 0:
#                 # Read the data and append it to the raw_data buffer
#                 data = bytearray(self.serial.read(self.serial.in_waiting))
#                 self.buffer_in.extend(data)
#                 # Detect all packet present in the buffer
#                 packet_detected = True
#                 while packet_detected:
#                     # Detect packet
#                     self.buffer_in, packet = parse_buffer(self.buffer_in)
#                     # Parse packet
#                     if len(packet) > 0:
#                         packet_detected = True
#                         logger.info(f"packet:{packet}")
#                         command, payload = parse_packet(packet)
#                         dict_dislay = {'command':command, 'payload':payload}
#                         self.data_ready.emit(dict_dislay)
#                     else:
#                         packet_detected = False

#     def write_serial(self, message):
#         self.serial.write(message.encode())



################################################################################
##                                   Turret                                   ##
################################################################################
class Turret():
    def __init__(self, port:str, baud_rate:int=115200):
        self.port=port
        self.baud_rate=baud_rate
        self.serial = serial.Serial(self.port, self.baud_rate)
        
        # internal variables
        self._pfm_to_int={'X':1, 'Y':2, 'Z':4, 'A':8,
                          'x':1, 'y':2, 'z':4, 'a':8}
        self._buffer = bytearray()
        
    def connect(self):
        self.serial.open()
        return self.serial.is_open
    
    def disconnect(self):
        self.serial.close()
        return ~self.serial.is_open
    
    def _check_integer(self, integer:int, bits:int, signed:bool):
        if signed:
            if bits==8:
                if -128 <= integer <= 127:
                    return True
                else:
                    return False
            if bits==16:
                if -32768 <= integer <= 32767:
                    return True
                else:
                    return False
            if bits==32:
                if -2147483648 <= integer <= 2147483647:
                    return True
                else:
                    return False
        else:
            if bits==8:
                if 0 <= integer <= 255:
                    return True
                else:
                    return False
            if bits==16:
                if 0 <= integer <= 65535:
                    return True
                else:
                    return False
            if bits==32:
                if 0 <= integer <= 4294967296:
                    return True
                else:
                    return False


    def _encode_message(self, payload):
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

    def _find_bytes(self, byte_array:bytearray, bytes:bytearray):
        """ Locate all indices of bytes-pattern within byte_array.

        :param byte_array: Array of bytes to be searched for a bytes-patter.
        :type byte_array: bytearray
        :param bytes: Patter of bytes to be searched for within byte_array.
        :type bytes: bytearray
        :return: List of indices, if no indices found returns [-1]
        :rtype: list
        """
        indices = []
        for i in range(len(byte_array)-1):
            if byte_array[i:i+len(bytes)] == bytes:
                indices.append(i)
        if len(indices) == 0:
            indices.append(-1)
        return indices

    def _parse_buffer(self, buffer:bytearray):
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
        packet_start_idxs = self._find_bytes(byte_array=buffer, bytes=START_BYTES)
        if packet_start_idxs[0] == -1:
            # no START_BYTES found, dump the buffer
            return bytearray(), bytearray()
        # detect all END_BYTES
        packet_end_idxs = self._find_bytes(byte_array=buffer, bytes=END_BYTES)
        # no END_BYTES found, return buffer to append more data
        if packet_end_idxs[0] == -1:
            return buffer, bytearray()
            
        # search for every start of the packet, until a packet of found
        for packet_start_idx in packet_start_idxs:
            for packet_end_idx in packet_end_idxs:
                expected_packet = buffer[packet_start_idx:packet_end_idx+len(END_BYTES)]
                packet_detected, packet = self._check_packet_complete(expected_packet)
                if packet_detected:
                    # remove the packet from the buffer
                    buffer = buffer[packet_end_idx+len(END_BYTES):]
                    return buffer, packet
                else:
                    # continue the search
                    pass
        return buffer, bytearray()


    def parse_packet(packet:bytearray):
        """ Break the packet into Command and Payload

        :param packet: Complete packet, including START_BYTES and END_BYTES
        :type packet: bytearray
        :return: Returns (Command, Payload_content) 
        :rtype: tuple(bytearray, bytearray)
        """
        command = packet[0:COMMAND_BYTE_SIZE]
        payload = packet[COMMAND_BYTE_SIZE:]
        return command, payload

    def _packet_incoming_to_dict(self, command, payload):
        info = dict()
        if command == CMD_SET_TARGET_FREQ:
            info['CMD'] = 'CMD_SET_TARGET_FREQ'
            info['ACK'] = True if int(payload[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
        elif command == CMD_SET_TARGET_DELTA:
            info['CMD'] = 'CMD_SET_TARGET_DELTA'
            info['ACK'] = True if int(payload[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
        elif command == CMD_GET_DELTA_STEPS:
            info['CMD'] = 'CMD_GET_DELTA_STEPS'
            if len(payload) > 1:
                info['DELTA'] = int.from_bytes(payload[0:4], byteorder=BYTEORDER)
            else:
                info['ACK'] = False if int(payload[0])==int.from_bytes(PKT_NACK, byteorder=BYTEORDER) else 'ERROR'
        elif command == CMD_GET_IMU_MEASUREMENT:
            info['CMD'] = 'CMD_GET_DELTA_STEPS'
            if len(payload) > 1:
                for idx, value_type in enumerate(['AX', 'AY', 'AZ', 'GX', 'GY', 'GZ', 'MX', 'MY', 'MZ']):
                    val_start = idx*2
                    val_end = val_start+2
                    info[value_type] = int.from_bytes(payload[val_start:val_end], byteorder=BYTEORDER)
            else:
                info['ACK'] = False if int(payload[0])==int.from_bytes(PKT_NACK, byteorder=BYTEORDER) else 'ERROR'
        elif command == CMD_SET_ISR_FREQ:
            info['CMD'] = 'CMD_SET_ISR_FREQ'
            if len(payload) > 1:
                info['ISR_FREQ'] = int.from_bytes(payload[0:2], byteorder=BYTEORDER)
            else:
                info['ACK'] = False if int(payload[0])==int.from_bytes(PKT_NACK, byteorder=BYTEORDER) else 'ERROR'
        elif command == CMD_ENABLE_CNC:
            info['CMD'] = 'CMD_ENABLE_CNC'
            info['ACK'] = True if int(payload[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
        elif command == CMD_DISABLE_CNC:
            info['CMD'] = 'CMD_DISABLE_CNC'
            info['ACK'] = True if int(payload[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
        elif command == CMD_SET_DELTA_STEPS:
            info['CMD'] = 'CMD_SET_DELTA_STEPS'
            info['ACK'] = True if int(payload[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
        else:
            raise ValueError(f"command={command}, invalid value.")
        return info

    def _which_pfm_to_int(self, which_pfm:str, raise_error:bool=True):
        if which_pfm.lower() not in self._pfm_to_int.keys():
            raise ValueError(f"which_pfm={which_pfm} is not valid, valid values ['X', 'Y', 'Z', 'A'] or ['x', 'y', 'z', 'a'].")
        return self._pfm_to_int[which_pfm]
    
    
    def _flush_serial_buffer(self):
        self._buffer = bytearray()
        
    
    def get_response(self, timeout_seconds:float=2.0):
        start_time = time.time()
        while time_elapsed < timeout_seconds:
            if self.serial.inWaiting() > 0:
                # Read the data and append it to the raw_data buffer
                data = bytearray(self.serial.read(self.serial.in_waiting))
                self._buffer.extend(data)
                # Detect all packet present in the buffer
                packet_detected = True
                while packet_detected:
                    # Detect packet
                    self._buffer, packet = self._parse_buffer(self._buffer)
                    # Parse packet
                    if len(packet) > 0:
                        packet_detected = True
                        command, payload = self._parse_packet(packet)
                        return {'command':command, 'payload':payload}
                    else:
                        packet_detected = False
            time_elapsed = time.time() - start_time
        # raise warning?
        # at least log an error
        return dict()
    
    def cmd_set_target_freq(self, which_pfm:str, freq:int, direction:bool, timeout_seconds:float=2.0, raise_error:bool=True):
        command = CMD_SET_TARGET_FREQ
        try:
            pmf_flag = self._which_pfm_to_int(which_pfm)
            if ~self._check_integer(integer=freq, bits=16, signed=False):
                raise ValueError(f"freq={freq} is 16 bit unsigned integer, valid values 0 <= freq <= 65535")
            payload = bytearray([
                    int.from_bytes(command, byteorder=BYTEORDER), # command
                    pmf_flag, # payload: which pfm
                    freq.to_bytes(2, byteorder=BYTEORDER)[0], # payload: freq lower
                    freq.to_bytes(2, byteorder=BYTEORDER)[1], # payload: freq ipper
                    int(direction), # payload: direction
                ])
            encoded_payload = self._encode_message(payload)
            self._flush_serial_buffer()
            self.serial.write(encoded_payload)
            dict_packet = self.get_response(timeout_seconds=timeout_seconds)
            return self._packet_incoming_to_dict(command=command, payload=dict_packet[payload])['ACK']
        except Exception as e:
            if raise_error:
                raise e
            else:
                return False

        
        
        
    
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
    
    
        
        
        
        
        
    # def send_block()
    
    
    
    
    
    
    
    

def encode_pfm_flag(PFM_X_FLAG:bool=False, PFM_Y_FLAG:bool=False, PFM_Z_FLAG:bool=False, PFM_Q_FLAG:bool=False):
    pmf_flag = 0b000
    if PFM_X_FLAG:
        pmf_flag = pmf_flag | 0b0001
    if PFM_Y_FLAG:
        pmf_flag = pmf_flag | 0b0010
    if PFM_Z_FLAG:
        pmf_flag = pmf_flag | 0b0100
    if PFM_Q_FLAG:
        pmf_flag = pmf_flag | 0b1000
    return pmf_flag


def decode_pfm_flag(pmf_flag):
    return {'PFM_X':bool(pmf_flag&0b0001),
            'PFM_Y':bool(pmf_flag&0b0010),
            'PFM_Z':bool(pmf_flag&0b0100),
            'PFM_Q':bool(pmf_flag&0b1000)}
    

def packet_outgoing_to_dict(command, payload):
    info = dict()
    # command_int = int.from_bytes(command, byteorder=BYTEORDER)
    if command == int.from_bytes(CMD_SET_TARGET_FREQ, byteorder=BYTEORDER):
        info['CMD'] = 'CMD_SET_TARGET_FREQ'
        info.update(decode_pfm_flag(payload[0]))
        info['FREQ'] = int.from_bytes(payload[1:3], byteorder=BYTEORDER)
        info['DIR'] = bool(payload[3])
    elif command == int.from_bytes(CMD_SET_TARGET_DELTA, byteorder=BYTEORDER):
        info['CMD'] = 'CMD_SET_TARGET_DELTA'
        info.update(decode_pfm_flag(payload[0]))
        info['FREQ'] = int.from_bytes(payload[1:3], byteorder=BYTEORDER)
        info['DELTA'] = int.from_bytes(payload[3:7], byteorder=BYTEORDER)
    elif command == int.from_bytes(CMD_GET_DELTA_STEPS, byteorder=BYTEORDER):
        info['CMD'] = 'CMD_GET_DELTA_STEPS'
        info.update(decode_pfm_flag(payload[0]))
    elif command == int.from_bytes(CMD_GET_IMU_MEASUREMENT, byteorder=BYTEORDER):
        info['CMD'] = 'CMD_GET_IMU_MEASUREMENT'
    elif command == int.from_bytes(CMD_SET_ISR_FREQ, byteorder=BYTEORDER):
        info['CMD'] = 'CMD_SET_ISR_FREQ'
        info['ISR_FREQ'] = int.from_bytes(payload[0:2], byteorder=BYTEORDER)
    elif command == int.from_bytes(CMD_ENABLE_CNC, byteorder=BYTEORDER):
        info['CMD'] = 'CMD_ENABLE_CNC'
    elif command == int.from_bytes(CMD_DISABLE_CNC, byteorder=BYTEORDER):
        info['CMD'] = 'CMD_DISABLE_CNC'
    elif command == int.from_bytes(CMD_SET_DELTA_STEPS, byteorder=BYTEORDER):
        info['CMD'] = 'CMD_SET_DELTA_STEPS'
        info.update(decode_pfm_flag(payload[0]))
        info['DELTA'] = int.from_bytes(payload[1:5], byteorder=BYTEORDER)
    else:
        raise ValueError(f"command={command}, invalid value.")
    return info
    
    
def packet_incoming_to_dict(command, payload):
    info = dict()
    if command == CMD_SET_TARGET_FREQ:
        info['CMD'] = 'CMD_SET_TARGET_FREQ'
        info['ACK'] = True if int(payload[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
    elif command == CMD_SET_TARGET_DELTA:
        info['CMD'] = 'CMD_SET_TARGET_DELTA'
        info['ACK'] = True if int(payload[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
    elif command == CMD_GET_DELTA_STEPS:
        info['CMD'] = 'CMD_GET_DELTA_STEPS'
        if len(payload) > 1:
            info['DELTA'] = int.from_bytes(payload[0:4], byteorder=BYTEORDER)
        else:
            info['ACK'] = False if int(payload[0])==int.from_bytes(PKT_NACK, byteorder=BYTEORDER) else 'ERROR'
    elif command == CMD_GET_IMU_MEASUREMENT:
        info['CMD'] = 'CMD_GET_DELTA_STEPS'
        if len(payload) > 1:
            for idx, value_type in enumerate(['AX', 'AY', 'AZ', 'GX', 'GY', 'GZ', 'MX', 'MY', 'MZ']):
                val_start = idx*2
                val_end = val_start+2
                info[value_type] = int.from_bytes(payload[val_start:val_end], byteorder=BYTEORDER)
        else:
            info['ACK'] = False if int(payload[0])==int.from_bytes(PKT_NACK, byteorder=BYTEORDER) else 'ERROR'
    elif command == CMD_SET_ISR_FREQ:
        info['CMD'] = 'CMD_SET_ISR_FREQ'
        if len(payload) > 1:
            info['ISR_FREQ'] = int.from_bytes(payload[0:2], byteorder=BYTEORDER)
        else:
            info['ACK'] = False if int(payload[0])==int.from_bytes(PKT_NACK, byteorder=BYTEORDER) else 'ERROR'
    elif command == CMD_ENABLE_CNC:
        info['CMD'] = 'CMD_ENABLE_CNC'
        info['ACK'] = True if int(payload[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
    elif command == CMD_DISABLE_CNC:
        info['CMD'] = 'CMD_DISABLE_CNC'
        info['ACK'] = True if int(payload[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
    elif command == CMD_SET_DELTA_STEPS:
        info['CMD'] = 'CMD_SET_DELTA_STEPS'
        info['ACK'] = True if int(payload[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
    else:
        raise ValueError(f"command={command}, invalid value.")
    return info
    
    
def cmd_dict_to_str(cmd_dict:dict):
    no_name_keys = ['CMD']
    pmf_flag_keys = ['PFM_X', 'PFM_Y', 'PFM_Z', 'PFM_Q']
    int_keys = ['FREQ', 'DELTA', 'ISR_FREQ']
    other_keys = ['DIR', 'ACK']
    imu_keys = ['AX', 'AY', 'AZ', 'GX', 'GY', 'GZ', 'MX', 'MY', 'MZ']
    
    string = ""
    for key, value in cmd_dict.items():
        if key in no_name_keys:
            string += f"{str(value)[4:].ljust(21)}: "
        if key in pmf_flag_keys:
            string += f"|{int(value)}"
        if key in int_keys:
            string += f" - {key}={str(value).ljust(6)}"
        if key in other_keys:
            string += f" - {key}={value}"
        if key in imu_keys:
            floating_point = (value-65535)/32767
            string += f"|{key}={floating_point:.2f}"
    return string
    

if __name__ == '__main__':
    
    BYTEORDER = 'little'

    payload = bytearray([
                1, # payload: which pfm
                11, # payload: freq
                0, # payload: freq
                1, # payload: pfm direction
                ],
            )
    command = CMD_SET_TARGET_FREQ

    print(packet_outgoing_to_dict(command, payload))
    print(cmd_dict_to_str(packet_outgoing_to_dict(command, payload)))
    
    payload = bytearray([
                1, 0,# AX
                2, 0,# AY
                3, 0,# AZ
                4, 0,# GX
                5, 0,# GY
                6, 0,# GZ
                7, 0,# MX
                8, 0,# MY
                9, 0,# MZ
                ],
            )
    command = CMD_GET_IMU_MEASUREMENT
    
    print(packet_incoming_to_dict(command, payload))
    print(cmd_dict_to_str(packet_incoming_to_dict(command, payload)))